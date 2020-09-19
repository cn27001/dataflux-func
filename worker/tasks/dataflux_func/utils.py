# -*- coding: utf-8 -*-

'''
杂项任务
包含各类清理类任务、DataFluxFuncAutoCleanerTask各类数据定时同步任务、数据源检查/调试任务等
'''

# Builtin Modules
import time
import json
import random
import traceback
import pprint

# 3rd-party Modules
import six
import simplejson
import ujson
import requests
import arrow

from six.moves.urllib_parse import urlsplit

# Project Modules
from worker import app
from worker.utils import toolkit, yaml_resources
from worker.tasks import gen_task_id, webhook
from worker.tasks.dataflux_func import gen_script_failure_id, gen_script_log_id, gen_data_source_id, decipher_data_source_config_fields
from worker.utils.extra_helpers import InfluxDBHelper

# Current Module
from worker.tasks import BaseTask
from worker.tasks.dataflux_func import ScriptCacherMixin, DATA_SOURCE_HELPER_CLASS_MAP

CONFIG = yaml_resources.get('CONFIG')

SCRIPT_MAP = {}

# DataFluxFunc.reloadScripts
class DataFluxFuncReloadScriptsTask(BaseTask, ScriptCacherMixin):
    '''
    脚本重新载入任务
    与 DataFluxFuncRunnerTask.update_script_dict_cache 配合完成高速脚本加载处理
    具体如下：
        1. 由于只有当用户「发布」脚本后，才需要重新加载，
           因此以 biz_main_func 表的最大 updateTime 作为是否需要重新读取数据库的标准
        2. 内存中维护 SCRIPT_MAP 作为缓存，结构如下：
           { "<脚本ID>": {完整脚本数据JSON} }
        3. 由于代码内容可能比较多，
           因此每次重新加载代码时，先只读取所有脚本的ID和MD5值，
           和内存中维护的 SCRIPT_MAP 对比获取需要更新的脚本ID列表
        4.1. 如果没有需要更新的脚本，则结束
        4.2. 如果存在需要更新的脚本，则从数据库中读取需要更新的脚本信息，并合并到 SCRIPT_MAP 中，
             最后更新整个脚本库和脚本库MD5缓存
        X.1. 附带强制重新加载功能
    '''

    def get_latest_publish_timestamp(self):
        sql = '''
            SELECT
                UNIX_TIMESTAMP(MAX(`updateTime`)) AS `timestamp`
            FROM biz_main_func
            '''
        db_res = self.db.query(sql)

        publish_timestamp = float(db_res[0]['timestamp'] or 0.0)

        return publish_timestamp

    def _cache_scripts(self):
        scripts = sorted(SCRIPT_MAP.values(), key=lambda x: x['seq'])
        scripts_dump = toolkit.json_safe_dumps(scripts, sort_keys=True)

        cache_key = toolkit.get_cache_key('fixedCache', 'scriptsMD5')
        self.cache_db.set(cache_key, toolkit.get_md5(scripts_dump))

        cache_key = toolkit.get_cache_key('fixedCache', 'scriptsDump')
        self.cache_db.set(cache_key, scripts_dump)

    def force_reload_script(self):
        global SCRIPT_MAP

        # 获取所有脚本
        scripts = self.get_scripts()
        for s in scripts:
            self.logger.debug('[SCRIPT CACHE] Load {}'.format(s['id']))

        # 字典化
        SCRIPT_MAP = dict([(s['id'], s) for s in scripts])

        # 3. Dump和MD5值写入缓存
        self._cache_scripts()

    def reload_script(self):
        global SCRIPT_MAP

        # 1. 获取当前所有脚本ID和MD5
        sql = '''
            SELECT
                 `scpt`.`id`
                ,`scpt`.`codeMD5`
                ,`scpt`.`publishVersion`
                ,`sset`.`id` AS `scriptSetId`
            FROM biz_main_script AS scpt

            JOIN biz_main_script_set as sset
            '''
        db_res = self.db.query(sql)

        current_script_ids = set()
        reload_script_ids  = set()
        for d in db_res:
            script_id  = d['id']

            current_script_ids.add(script_id)
            cached_script = SCRIPT_MAP.get(script_id)

            if not cached_script:
                # 新脚本
                reload_script_ids.add(script_id)

            elif cached_script['codeMD5'] != d['codeMD5'] or cached_script['publishVersion'] != d['publishVersion']:
                # 更新脚本
                reload_script_ids.add(script_id)

        # 去除已经不存在的脚本
        script_ids_to_pop = []
        for script_id in SCRIPT_MAP.keys():
            if script_id not in current_script_ids:
                self.logger.debug('[SCRIPT CACHE] Remove {}'.format(script_id))
                script_ids_to_pop.append(script_id)

        for script_id in script_ids_to_pop:
            SCRIPT_MAP.pop(script_id, None)

        if reload_script_ids:
            # 2. 从数据库获取更新后的脚本
            scripts = self.get_scripts(script_ids=reload_script_ids)
            for s in scripts:
                self.logger.debug('[SCRIPT CACHE] Load {}'.format(s['id']))

            # 合并加载的脚本
            reloaded_script_map = dict([(s['id'], s) for s in scripts])
            SCRIPT_MAP.update(reloaded_script_map)

            # 3. Dump和MD5值写入缓存
            self._cache_scripts()

            # 4. 删除函数结果缓存
            for script_id in reload_script_ids:
                func_id_pattern = '{0}.*'.format(script_id)
                cache_key = toolkit.get_cache_key('cache', 'funcResult', tags=[
                    'funcId', func_id_pattern,
                    'scriptCodeMD5', '*',
                    'funcKwargsMD5', '*'])
                for k in self.cache_db.client.scan_iter(cache_key):
                    self.cache_db.delete(six.ensure_str(k))

@app.task(name='DataFluxFunc.reloadScripts', bind=True, base=DataFluxFuncReloadScriptsTask)
def dataflux_func_reload_scripts(self, *args, **kwargs):
    is_startup = kwargs.get('isStartUp') or False
    force      = kwargs.get('force')     or False

    if is_startup:
        lock_key   = toolkit.get_cache_key('lock', 'reloadScripts')
        lock_value = toolkit.gen_uuid()
        if not self.cache_db.lock(lock_key, lock_value, 10):
            self.logger.warning('DataFluxFunc ReloadScriptDict Task already launched.')
            return

    self.logger.info('DataFluxFunc ReloadScriptDict Task launched.')

    cache_key = toolkit.get_cache_key('fixedCache', 'prevDBUpdateTimestamp')

    # 上次脚本更新时间
    prev_publish_timestamp = float(self.cache_db.get(cache_key) or 0.0)
    if not prev_publish_timestamp:
        force = True

    # 最近脚本更新时间
    latest_publish_timestamp = self.get_latest_publish_timestamp()

    is_script_reloaded = False
    if force:
        self.force_reload_script()
        is_script_reloaded = True

    elif latest_publish_timestamp != prev_publish_timestamp:
        self.reload_script()
        is_script_reloaded = True

    if is_script_reloaded:
        self.logger.debug('[SCRIPT CACHE] Reload script {} -> {} {}'.format(
            arrow.get(prev_publish_timestamp).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss'),
            arrow.get(latest_publish_timestamp).to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss'),
            '[FORCE]' if force else ''))

        self.cache_db.set(cache_key, str(latest_publish_timestamp))

# DataFluxFunc.syncCache
class DataFluxFuncSyncCache(BaseTask):
    def sync_script_running_info(self):
        data = []

        # 搜集数据
        cache_key = toolkit.get_cache_key('syncCache', 'scriptRunningInfo')
        for i in range(CONFIG['_BUILTIN_TASK_SYNC_CACHE_BATCH_COUNT']):
            cache_res = self.cache_db.run('rpop', cache_key)
            if not cache_res:
                break

            try:
                cache_res = ujson.loads(cache_res)
            except Exception as e:
                for line in traceback.format_exc().splitlines():
                    self.logger.error(line)
            else:
                data.append(cache_res)

        # 分类计算
        data_map = {}
        for d in data:
            func_id                = d['funcId']
            script_publish_version = d['scriptPublishVersion']
            exec_mode              = d['execMode']
            is_failed              = d['isFailed']
            cost                   = int(d['cost'] * 1000)
            timestamp              = d.get('timestamp')

            if not timestamp:
                continue

            if exec_mode is None:
                exec_mode = 'sync'

            pk = '~'.join([func_id, str(script_publish_version), exec_mode])
            if pk not in data_map:
                data_map[pk] = {
                    'funcId'              : func_id,
                    'scriptPublishVersion': script_publish_version,
                    'execMode'            : exec_mode,
                }

            if 'succeedCount' not in data_map[pk]:
                data_map[pk]['succeedCount'] = 0

            if 'failCount' not in data_map[pk]:
                data_map[pk]['failCount'] = 0

            data_map[pk]['latestFailTimestamp']    = None
            data_map[pk]['latestSucceedTimestamp'] = None

            if is_failed:
                data_map[pk]['failCount']           += 1
                data_map[pk]['latestFailTimestamp'] = timestamp
                data_map[pk]['status']              = 'failed'
            else:
                data_map[pk]['succeedCount']           += 1
                data_map[pk]['latestSucceedTimestamp'] = timestamp
                data_map[pk]['status']                 = 'succeeded'

            if 'minCost' not in data_map[pk]:
                data_map[pk]['minCost'] = cost
            else:
                data_map[pk]['minCost'] = min(data_map[pk]['minCost'], cost)

            if 'maxCost' not in data_map[pk]:
                data_map[pk]['maxCost'] = cost
            else:
                data_map[pk]['maxCost'] = max(data_map[pk]['maxCost'], cost)

            if 'totalCost' not in data_map[pk]:
                data_map[pk]['totalCost'] = cost
            else:
                data_map[pk]['totalCost'] += cost

            data_map[pk]['latestCost'] = cost

        # 分类入库
        for pk, d in data_map.items():
            func_id   = d['funcId']
            exec_mode = d['execMode']

            sql = '''
                SELECT
                     `succeedCount`
                    ,`failCount`
                    ,`minCost`
                    ,`maxCost`
                    ,`totalCost`
                    ,`latestCost`
                    ,UNIX_TIMESTAMP(`latestSucceedTime`) AS `latestSucceedTimestamp`
                    ,UNIX_TIMESTAMP(`latestFailTime`)    AS `latestFailTimestamp`
                    ,`status`
                FROM biz_rel_func_running_info
                WHERE
                        `funcId`               = ?
                    AND `scriptPublishVersion` = ?
                    AND `execMode`             = ?
                LIMIT 1
                '''
            sql_params = [
                func_id,
                script_publish_version,
                exec_mode,
            ]
            prev_info = self.db.query(sql, sql_params)

            if not prev_info:
                # 无记录，则补全记录
                sql = '''
                    INSERT IGNORE INTO biz_rel_func_running_info
                    SET
                       `funcId`               = ?
                      ,`scriptPublishVersion` = ?
                      ,`execMode`             = ?

                      ,`succeedCount`      = ?
                      ,`failCount`         = ?
                      ,`minCost`           = ?
                      ,`maxCost`           = ?
                      ,`totalCost`         = ?
                      ,`latestCost`        = ?
                      ,`latestSucceedTime` = FROM_UNIXTIME(?)
                      ,`latestFailTime`    = FROM_UNIXTIME(?)
                      ,`status`            = ?
                '''
                sql_params = [
                    func_id,
                    script_publish_version,
                    exec_mode,

                    d['succeedCount'],
                    d['failCount'],
                    d['minCost'],
                    d['maxCost'],
                    d['totalCost'],
                    d['latestCost'],
                    d['latestSucceedTimestamp'],
                    d['latestFailTimestamp'],
                    d['status'],
                ]
                self.db.query(sql, sql_params)

            else:
                prev_info = prev_info[0]

                # 有记录，合并
                sql = '''
                    UPDATE biz_rel_func_running_info
                    SET
                         `succeedCount`      = ?
                        ,`failCount`         = ?
                        ,`minCost`           = ?
                        ,`maxCost`           = ?
                        ,`totalCost`         = ?
                        ,`latestCost`        = ?
                        ,`latestSucceedTime` = FROM_UNIXTIME(?)
                        ,`latestFailTime`    = FROM_UNIXTIME(?)
                        ,`status`            = ?

                    WHERE
                            `funcId`               = ?
                        AND `scriptPublishVersion` = ?
                        AND `execMode`             = ?
                    LIMIT 1
                '''
                sql_params = [
                    d['succeedCount'] + (prev_info['succeedCount'] or 0),
                    d['failCount']    + (prev_info['failCount']    or 0),
                    min(filter(lambda x: x is not None, (d['minCost'], prev_info['minCost']))),
                    max(filter(lambda x: x is not None, (d['maxCost'], prev_info['maxCost']))),
                    d['totalCost'] + (prev_info['totalCost'] or 0),
                    d['latestCost'],
                    d['latestSucceedTimestamp'] or prev_info['latestSucceedTimestamp'],
                    d['latestFailTimestamp']    or prev_info['latestFailTimestamp'],
                    d['status'],

                    func_id,
                    script_publish_version,
                    exec_mode,
                ]
                self.db.query(sql, sql_params)

    def sync_script_failure(self):
        cache_key = toolkit.get_cache_key('syncCache', 'scriptFailure')

        for i in range(CONFIG['_BUILTIN_TASK_SYNC_CACHE_BATCH_COUNT']):
            cache_res = self.cache_db.run('rpop', cache_key)
            if not cache_res:
                break

            try:
                cache_res = ujson.loads(cache_res)
            except Exception as e:
                for line in traceback.format_exc().splitlines():
                    self.logger.error(line)

                continue

            func_id                = cache_res['funcId']
            script_publish_version = cache_res['scriptPublishVersion']
            exec_mode              = cache_res['execMode']
            einfo_text             = cache_res.get('einfoTEXT')
            trace_info             = cache_res.get('traceInfo')
            timestamp              = cache_res.get('timestamp')

            if not all([einfo_text, timestamp]):
                continue

            if exec_mode is None:
                exec_mode = 'sync'

            # 记录脚本故障
            failure_id = gen_script_failure_id()

            exception = None
            if trace_info:
                exception = trace_info.get('exceptionDump') or ''
                if isinstance(exception, six.string_types):
                    exception = exception.split(':')[0]
                else:
                    exception = None

                trace_info = simplejson.dumps(trace_info, default=toolkit.json_dump_default)

            sql = '''
                INSERT INTO biz_main_script_failure
                SET
                   `id`                   = ?
                  ,`funcId`               = ?
                  ,`scriptPublishVersion` = ?
                  ,`execMode`             = ?
                  ,`einfoTEXT`            = ?
                  ,`exception`            = ?
                  ,`traceInfoJSON`        = ?
                  ,`createTime`           = FROM_UNIXTIME(?)
                  ,`updateTime`           = FROM_UNIXTIME(?)
            '''
            sql_params = [
                failure_id,
                func_id,
                script_publish_version,
                exec_mode,
                einfo_text,
                exception,
                trace_info,
                timestamp, timestamp,
            ]
            self.db.query(sql, sql_params)

    def sync_script_log(self):
        cache_key = toolkit.get_cache_key('syncCache', 'scriptLog')

        # 当队列数量过大时，一些内容不再记录
        queue_length = 0
        cache_res = self.cache_db.run('llen', cache_key)
        if cache_res:
            queue_length = int(cache_res)

        is_service_degraded = queue_length > CONFIG['_BUILTIN_TASK_SYNC_CACHE_SERVICE_DEGRADE_QUEUE_LENGTH']

        for i in range(CONFIG['_BUILTIN_TASK_SYNC_CACHE_BATCH_COUNT']):
            cache_res = self.cache_db.run('rpop', cache_key)
            if not cache_res:
                break

            # 发生服务降级时，随机丢弃
            if is_service_degraded:
                if random.randint(0, queue_length) * 2 > CONFIG['_BUILTIN_TASK_SYNC_CACHE_SERVICE_DEGRADE_QUEUE_LENGTH']:
                    continue

            try:
                cache_res = ujson.loads(cache_res)
            except Exception as e:
                for line in traceback.format_exc().splitlines():
                    self.logger.error(line)

                continue

            func_id                = cache_res['funcId']
            script_publish_version = cache_res['scriptPublishVersion']
            exec_mode              = cache_res['execMode']
            log_messages           = cache_res.get('logMessages')
            timestamp              = cache_res.get('timestamp')

            if not all([log_messages, timestamp]):
                continue

            if exec_mode is None:
                exec_mode = 'sync'

            # 记录脚本日志
            log_id = gen_script_log_id()

            message_text = '\n'.join(log_messages).strip()

            sql = '''
                INSERT INTO biz_main_script_log
                SET
                   `id`                   = ?
                  ,`funcId`               = ?
                  ,`scriptPublishVersion` = ?
                  ,`execMode`             = ?
                  ,`messageTEXT`          = ?
                  ,`createTime`           = FROM_UNIXTIME(?)
                  ,`updateTime`           = FROM_UNIXTIME(?)
            '''
            sql_params = [
                log_id,
                func_id,
                script_publish_version,
                exec_mode,
                message_text,
                timestamp, timestamp,
            ]
            self.db.query(sql, sql_params)

    def sync_task_info(self):
        cache_key = toolkit.get_cache_key('syncCache', 'taskInfo')

        # 当队列数量过大时，一些内容不再记录
        queue_length = 0
        cache_res = self.cache_db.run('llen', cache_key)
        if cache_res:
            queue_length = int(cache_res)

        is_service_degraded = queue_length > CONFIG['_BUILTIN_TASK_SYNC_CACHE_SERVICE_DEGRADE_QUEUE_LENGTH']

        for i in range(CONFIG['_BUILTIN_TASK_SYNC_CACHE_BATCH_COUNT']):
            cache_res = self.cache_db.run('rpop', cache_key)
            if not cache_res:
                break

            try:
                cache_res = ujson.loads(cache_res)
            except Exception as e:
                for line in traceback.format_exc().splitlines():
                    self.logger.error(line)
                continue

            task_id                = cache_res['taskId']
            origin                 = cache_res['origin']
            origin_id              = cache_res['originId']
            func_id                = cache_res.get('funcId')
            script_publish_version = cache_res.get('scriptPublishVersion')
            status                 = cache_res['status']
            log_messages           = cache_res.get('logMessages') or []
            einfo_text             = cache_res.get('einfoTEXT')   or ''
            timestamp              = cache_res.get('timestamp')

            if not all([origin, origin_id, timestamp]):
                continue

            if origin not in ('crontab', 'batch'):
                continue

            message_text = '\n'.join(log_messages).strip()

            # 记录任务信息
            table_name      = None
            origin_id_field = None
            if origin == 'crontab':
                table_name      = 'biz_main_crontab_task_info'
                origin_id_field = 'crontabConfigId'

            elif origin == 'batch':
                table_name      = 'biz_main_batch_task_info'
                origin_id_field = 'batchId'

            sql        = None
            sql_params = None

            # 根据是否服务降级区分处理
            if not is_service_degraded:
                # 未发生服务降级，正常处理
                if status == 'queued':
                    sql = '''
                        INSERT INTO ??
                        SET
                             `id`                   = ?
                            ,`??`                   = ?
                            ,`funcId`               = ?
                            ,`scriptPublishVersion` = ?
                            ,`queueTime`            = FROM_UNIXTIME(?)
                            ,`createTime`           = FROM_UNIXTIME(?)
                            ,`updateTime`           = FROM_UNIXTIME(?)
                        '''
                    sql_params = [
                        table_name,
                        task_id,
                        origin_id_field, origin_id,
                        func_id,
                        script_publish_version,
                        timestamp, timestamp, timestamp,
                    ]

                elif status == 'pending':
                    sql = '''
                        UPDATE ??
                        SET
                             `funcId`               = IFNULL(?, `funcId`)
                            ,`scriptPublishVersion` = IFNULL(?, `scriptPublishVersion`)
                            ,`startTime`  = FROM_UNIXTIME(?)
                            ,`status`     = ?
                            ,`updateTime` = FROM_UNIXTIME(?)
                        WHERE
                            `id` = ?
                        '''
                    sql_params = [
                        table_name,

                        func_id,
                        script_publish_version,
                        timestamp,
                        status,
                        timestamp,
                        task_id
                    ]

                else:
                    sql = '''
                        UPDATE ??
                        SET
                             `funcId`               = IFNULL(?, `funcId`)
                            ,`scriptPublishVersion` = IFNULL(?, `scriptPublishVersion`)
                            ,`endTime`              = FROM_UNIXTIME(?)
                            ,`status`               = ?
                            ,`logMessageTEXT`       = ?
                            ,`einfoTEXT`            = ?
                            ,`updateTime`           = FROM_UNIXTIME(?)
                        WHERE
                            `id` = ?
                        '''
                    sql_params = [
                        table_name,

                        func_id,
                        script_publish_version,
                        timestamp,
                        status,
                        message_text,
                        einfo_text,
                        timestamp,
                        task_id,
                    ]

            else:
                # 发生服务降级，处理最终结果
                if status in ('success', 'failure'):
                    sql = '''
                        REPLACE INTO ??
                        SET
                             `id`                   = ?
                            ,`??`                   = ?
                            ,`funcId`               = ?
                            ,`scriptPublishVersion` = ?
                            ,`endTime`              = FROM_UNIXTIME(?)
                            ,`status`               = ?
                            ,`logMessageTEXT`       = ?
                            ,`einfoTEXT`            = ?
                            ,`createTime`           = FROM_UNIXTIME(?)
                            ,`updateTime`           = FROM_UNIXTIME(?)
                        '''
                    sql_params = [
                        table_name,
                        task_id,
                        origin_id_field, origin_id,
                        func_id,
                        script_publish_version,
                        timestamp,
                        status,
                        message_text,
                        einfo_text,
                        timestamp, timestamp,
                    ]

                else:
                    continue

            self.db.query(sql, sql_params)

@app.task(name='DataFluxFunc.syncCache', bind=True, base=DataFluxFuncSyncCache)
def dataflux_func_sync_cache(self, *args, **kwargs):
    lock_key   = toolkit.get_cache_key('lock', 'syncCache')
    lock_value = toolkit.gen_uuid()
    if not self.cache_db.lock(lock_key, lock_value, 30):
        self.logger.warning('DataFluxFunc SyncCache Task already launched.')
        return

    self.logger.info('DataFluxFunc SyncCache Task launched.')

    # 脚本运行信息刷入数据库
    try:
        self.sync_script_running_info()
    except Exception as e:
        for line in traceback.format_exc().splitlines():
            self.logger.error(line)

    # 脚本失败信息刷入数据库
    try:
        self.sync_script_failure()
    except Exception as e:
        for line in traceback.format_exc().splitlines():
            self.logger.error(line)

    # 脚本日志刷入数据库
    try:
        self.sync_script_log()
    except Exception as e:
        for line in traceback.format_exc().splitlines():
            self.logger.error(line)

    # 任务信息刷入数据库
    try:
        self.sync_task_info()
    except Exception as e:
        for line in traceback.format_exc().splitlines():
            self.logger.error(line)

# DataFluxFunc.autoCleaner
class DataFluxFuncAutoCleanerTask(BaseTask):
    def _delete_by_seq(self, table, seq):
        sql = '''
            DELETE FROM ??
            WHERE
                `seq` <= ?;
            '''
        sql_params = [table, seq]
        self.db.query(sql, sql_params)

    def clear_table_by_limit(self, table, limit):
        sql = '''
            SELECT
                `seq`
            FROM ??
            ORDER BY
                `seq` DESC
            LIMIT ?, 1;
            '''
        sql_params = [table, limit]
        db_res = self.db.query(sql, sql_params)
        if db_res:
            self._delete_by_seq(table, db_res[0]['seq'])

    def clear_table_by_expires(self, table, expires):
        sql = '''
            SELECT
                `seq`
            FROM ??
            WHERE
                UNIX_TIMESTAMP(`createTime`) < UNIX_TIMESTAMP() - ?
            ORDER BY
                `seq` DESC
            LIMIT 1;
            '''
        sql_params = [table, expires]
        db_res = self.db.query(sql, sql_params)
        if db_res:
            self._delete_by_seq(table, db_res[0]['seq'])

@app.task(name='DataFluxFunc.autoCleaner', bind=True, base=DataFluxFuncAutoCleanerTask)
def dataflux_func_auto_cleaner(self, *args, **kwargs):
    lock_key   = toolkit.get_cache_key('lock', 'autoCleaner')
    lock_value = toolkit.gen_uuid()
    if not self.cache_db.lock(lock_key, lock_value, 30):
        self.logger.warning('DataFluxFunc AutoCleaner Task already launched.')
        return

    self.logger.info('DataFluxFunc AutoCleaner Task launched.')

    # 清除脚本日志
    script_log_limit = CONFIG['_DBDATA_SCRIPT_LOG_LIMIT']
    try:
        self.clear_table_by_limit(table='biz_main_script_log', limit=script_log_limit)
    except Exception as e:
        for line in traceback.format_exc().splitlines():
            self.logger.error(line)

    # 清除脚本错误记录
    script_failure_limit = CONFIG['_DBDATA_SCRIPT_FAILURE_LIMIT']
    try:
        self.clear_table_by_limit(table='biz_main_script_failure', limit=script_failure_limit)
    except Exception as e:
        for line in traceback.format_exc().splitlines():
            self.logger.error(line)

    # 清除函数结果
    func_result_limit = CONFIG['_DBDATA_FUNC_RESULT_LIMIT']
    try:
        self.clear_table_by_limit(table='biz_main_task_result_dataflux_func', limit=func_result_limit)
    except Exception as e:
        for line in traceback.format_exc().splitlines():
            self.logger.error(line)

    # 清除自动触发任务记录
    crontab_task_info_limit = CONFIG['_DBDATA_CRONTAB_TASK_INFO_LIMIT']
    try:
        self.clear_table_by_limit(table='biz_main_crontab_task_info', limit=crontab_task_info_limit)
    except Exception as e:
        for line in traceback.format_exc().splitlines():
            self.logger.error(line)

    # 清除批处理任务记录
    batch_task_info_limit = CONFIG['_DBDATA_BATCH_TASK_INFO_LIMIT']
    try:
        self.clear_table_by_limit(table='biz_main_batch_task_info', limit=batch_task_info_limit)
    except Exception as e:
        for line in traceback.format_exc().splitlines():
            self.logger.error(line)

    # 清除操作记录
    operation_record_limit = CONFIG['_DBDATA_OPERATION_RECORD_LIMIT']
    try:
        self.clear_table_by_limit(table='biz_main_operation_record', limit=operation_record_limit)
    except Exception as e:
        for line in traceback.format_exc().splitlines():
            self.logger.error(line)

# DataFluxFunc.dataSourceChecker
@app.task(name='DataFluxFunc.dataSourceChecker', bind=True, base=BaseTask)
def dataflux_func_data_source_checker(self, *args, **kwargs):
    self.logger.info('DataFluxFunc DataSource Checker Task launched.')

    data_source_type   = kwargs.get('type')
    data_source_config = kwargs.get('config')

    # 检查数据源
    data_source_helper_class = DATA_SOURCE_HELPER_CLASS_MAP.get(data_source_type)
    if not data_source_helper_class:
        e = Exception('Unsupported DataSource type: `{}`'.format(data_source_type))
        raise e

    data_source_helper = data_source_helper_class(self.logger, config=data_source_config)

    data_source_helper.check()

# DataFluxFunc.dataSourceDebugger
@app.task(name='DataFluxFunc.dataSourceDebugger', bind=True, base=BaseTask)
def dataflux_func_data_source_debugger(self, *args, **kwargs):
    self.logger.info('DataFluxFunc DataSource Debugger Task launched.')

    data_source_id = kwargs.get('id')
    command        = kwargs.get('command')
    command_args   = kwargs.get('commandArgs')   or []
    command_kwargs = kwargs.get('commandKwargs') or {}
    return_type    = kwargs.get('returnType')    or 'json'

    data_source = None

    # 查询数据源
    sql = '''
        SELECT
            `type`,
            `configJSON`
        FROM biz_main_data_source
        WHERE
            `id` = ?
        '''
    sql_params = [data_source_id]
    db_res = self.db.query(sql, sql_params)
    if len(db_res) > 0:
        data_source = db_res[0]
        data_source['config'] = ujson.loads(data_source['configJSON'])

    if not data_source:
        e = Exception('No such DataSource')
        raise e

    # 执行数据源命令
    data_source_type   = data_source.get('type')
    data_source_config = data_source.get('config')
    data_source_config = decipher_data_source_config_fields(data_source_config)

    data_source_helper_class = DATA_SOURCE_HELPER_CLASS_MAP.get(data_source_type)
    if not data_source_helper_class:
        e = Exception('Unsupported DataSource type: `{}`'.format(da))
        raise e

    # 解密字段
    data_source_helper = data_source_helper_class(self.logger, config=data_source_config)

    db_res = getattr(data_source_helper, command)(*command_args, **command_kwargs)

    ret = None
    if return_type == 'repr':
        ret = pprint.pformat(db_res, width=100)
    else:
        ret = db_res
    return ret

# DataFluxFunc.getSystemConfig
@app.task(name='DataFluxFunc.getSystemConfig', bind=True, base=BaseTask)
def dataflux_func_get_system_config(self, *args, **kwargs):
    system_config = {
        '_FUNC_TASK_DEFAULT_TIMEOUT'     : CONFIG['_FUNC_TASK_DEFAULT_TIMEOUT'],
        '_CRONTAB_STARTER'               : CONFIG['_CRONTAB_STARTER'],
        '_CRONTAB_AUTO_CLEANER'          : CONFIG['_CRONTAB_AUTO_CLEANER'],
        '_DBDATA_SCRIPT_LOG_LIMIT'       : CONFIG['_DBDATA_SCRIPT_LOG_LIMIT'],
        '_DBDATA_SCRIPT_FAILURE_LIMIT'   : CONFIG['_DBDATA_SCRIPT_FAILURE_LIMIT'],
        '_DBDATA_FUNC_RESULT_LIMIT'      : CONFIG['_DBDATA_FUNC_RESULT_LIMIT'],
        '_DBDATA_CRONTAB_TASK_INFO_LIMIT': CONFIG['_DBDATA_CRONTAB_TASK_INFO_LIMIT'],
        '_DBDATA_BATCH_TASK_INFO_LIMIT'  : CONFIG['_DBDATA_BATCH_TASK_INFO_LIMIT'],
        '_DBDATA_OPERATION_RECORD_LIMIT' : CONFIG['_DBDATA_OPERATION_RECORD_LIMIT'],
    }
    return system_config

# 启动时自动执行（已附带锁）
# dataflux_func_reload_scripts.apply_async(kwargs={'isStartUp': True, 'force': True, 'startup_sleep': 10})
# dataflux_func_auto_cleaner.apply_async(kwargs={'startup_sleep': 30})
