import Vue from 'vue'
import VueRouter from 'vue-router'
import store from '@/store'

import * as toolkit from '@/toolkit'

const originalPush = VueRouter.prototype.push;
VueRouter.prototype.push = function push(location) {
  return originalPush.call(this, location).catch(err => err);
}

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    redirect: '/index',
  },
  {
    path: '/index',
    name: 'index',
    component: () => import('../views/Index.vue'),
  },
  {
    path: '/sign-out',
    name: 'sign-out',
    component: () => import('../views/SignOut.vue'),
  },
  {
    path: '/editor',
    component: () => import('../views/Editor.vue'),
    children: [
      {
        path: 'intro',
        name: 'intro',
        component: () => import('../components/Editor/Intro.vue'),
      },
      {
        path: 'code-editor/:id',
        name: 'code-editor',
        component: () => import('../components/Editor/CodeEditor.vue'),
      },
      {
        path: 'code-viewer/:id',
        name: 'code-viewer',
        component: () => import('../components/Editor/CodeViewer.vue'),
      },
      {
        path: 'script-set-add',
        name: 'script-set-add',
        component: () => import('../components/Editor/ScriptSetSetup.vue'),
      },
      {
        path: 'script-set/:id/setup',
        name: 'script-set-setup',
        component: () => import('../components/Editor/ScriptSetSetup.vue'),
      },
      {
        path: 'script-set/:id/add-script',
        name: 'script-add',
        component: () => import('../components/Editor/ScriptSetup.vue'),
      },
      {
        path: 'script/:id/setup',
        name: 'script-setup',
        component: () => import('../components/Editor/ScriptSetup.vue'),
      },
      {
        path: 'data-source-add',
        name: 'data-source-add',
        component: () => import('../components/Editor/DataSourceSetup.vue'),
      },
      {
        path: 'data-source/:id/setup',
        name: 'data-source-setup',
        component: () => import('../components/Editor/DataSourceSetup.vue'),
      },
      {
        path: 'env-variable-add',
        name: 'env-variable-add',
        component: () => import('../components/Editor/EnvVariableSetup.vue'),
      },
      {
        path: 'env-variable/:id/setup',
        name: 'env-variable-setup',
        component: () => import('../components/Editor/EnvVariableSetup.vue'),
      },
    ]
  },
  {
    path: '/management',
    name: 'management',
    component: () => import('../views/Management.vue'),
    children: [
      {
        path: 'overview',
        name: 'overview',
        component: () => import('../components/Management/Overview.vue'),
      },
      {
        path: 'about',
        name: 'about',
        component: () => import('../components/Management/About.vue'),
      },
      {
        path: 'auth-link-list',
        name: 'auth-link-list',
        component: () => import('../components/Management/AuthLinkList.vue'),
      },
      {
        path: 'auth-link-add',
        name: 'auth-link-add',
        component: () => import('../components/Management/AuthLinkSetup.vue'),
      },
      {
        path: 'auth-link/:id/setup',
        name: 'auth-link-setup',
        component: () => import('../components/Management/AuthLinkSetup.vue'),
      },

      {
        path: 'crontab-config-list',
        name: 'crontab-config-list',
        component: () => import('../components/Management/CrontabConfigList.vue'),
      },
      {
        path: 'crontab-config-add',
        name: 'crontab-config-add',
        component: () => import('../components/Management/CrontabConfigSetup.vue'),
      },
      {
        path: 'crontab-config/:id/setup',
        name: 'crontab-config-setup',
        component: () => import('../components/Management/CrontabConfigSetup.vue'),
      },
      {
        path: 'crontab/:id/task-info-list',
        name: 'crontab-task-info-list',
        component: () => import('../components/Management/CrontabTaskInfoList.vue'),
      },

      {
        path: 'batch-list',
        name: 'batch-list',
        component: () => import('../components/Management/BatchList.vue'),
      },
      {
        path: 'batch-add',
        name: 'batch-add',
        component: () => import('../components/Management/BatchSetup.vue'),
      },
      {
        path: 'batch/:id/setup',
        name: 'batch-setup',
        component: () => import('../components/Management/BatchSetup.vue'),
      },
      {
        path: 'batch/:id/task-info-list',
        name: 'batch-task-info-list',
        component: () => import('../components/Management/BatchTaskInfoList.vue'),
      },

      {
        path: 'script-set-export-history-list',
        name: 'script-set-export-history-list',
        component: () => import('../components/Management/ScriptSetExportHistoryList.vue'),
      },
      {
        path: 'script-set-export',
        name: 'script-set-export',
        component: () => import('../components/Management/ScriptSetExport.vue'),
      },
      {
        path: 'script-set-import-history-list',
        name: 'script-set-import-history-list',
        component: () => import('../components/Management/ScriptSetImportHistoryList.vue'),
      },
      {
        path: 'script-set-import',
        name: 'script-set-import',
        component: () => import('../components/Management/ScriptSetImport.vue'),
      },

      {
        path: 'script-recover-point-list',
        name: 'script-recover-point-list',
        component: () => import('../components/Management/ScriptRecoverPointList.vue'),
      },
      {
        path: 'script-recover-point-add',
        name: 'script-recover-point-add',
        component: () => import('../components/Management/ScriptRecoverPointAdd.vue'),
      },

      {
        path: 'user-list',
        name: 'user-list',
        component: () => import('../components/Management/UserList.vue'),
      },
      {
        path: 'user-add',
        name: 'user-add',
        component: () => import('../components/Management/UserSetup.vue'),
      },
      {
        path: 'user/:id/setup',
        name: 'user-setup',
        component: () => import('../components/Management/UserSetup.vue'),
      },

      {
        path: 'operation-record-list',
        name: 'operation-record-list',
        component: () => import('../components/Management/OperationRecordList.vue'),
      },

      {
        path: 'script-log-list',
        name: 'script-log-list',
        component: () => import('../components/Management/ScriptLogList.vue'),
      },
      {
        path: 'script-failure-list',
        name: 'script-failure-list',
        component: () => import('../components/Management/ScriptFailureList.vue'),
      },

      {
        path: 'experimental-features',
        name: 'experimental-features',
        component: () => import('../components/Management/ExperimentalFeatures.vue'),
      },
      {
        path: 'access-key-list',
        name: 'access-key-list',
        component: () => import('../components/Management/AccessKeyList.vue'),
      },
      {
        path: 'access-key-add',
        name: 'access-key-add',
        component: () => import('../components/Management/AccessKeySetup.vue'),
      },
      {
        path: 'sys-stats',
        name: 'sys-stats',
        component: () => import('../components/Management/SysStats.vue'),
      },
      {
        path: 'pip-tool',
        name: 'pip-tool',
        component: () => import('../components/Management/PIPTool.vue'),
      },
      {
        path: 'file-tool',
        name: 'file-tool',
        component: () => import('../components/Management/FileTool.vue'),
      },
    ],
  },
  {
    path: '/setting',
    name: 'setting',
    component: () => import('../views/Setting.vue'),
    children: [
      {
        path: 'clear-cache',
        name: 'clear-cache',
        component: () => import('../components/Setting/ClearCache.vue'),
      },
      {
        path: 'code-editor-setup',
        name: 'code-editor-setup',
        component: () => import('../components/Setting/CodeEditorSetup.vue'),
      },
      {
        path: 'profile-setup',
        name: 'profile-setup',
        component: () => import('../components/Setting/ProfileSetup.vue'),
      },
      {
        path: 'password-setup',
        name: 'password-setup',
        component: () => import('../components/Setting/PasswordSetup.vue'),
      },
    ],
  },
  {
    path: '/func-doc',
    name: 'func-doc',
    component: () => import('../views/FuncDoc.vue'),
  },
  {
    path: '/auth-link-func-doc',
    name: 'auth-link-func-doc',
    component: () => import('../views/AuthLinkFuncDoc.vue'),
  },
  {
    path: '/dream',
    name: 'dream',
    component: () => import('../views/Dream.vue'),
  },
];

const router = new VueRouter({
  routes,
});

router.beforeEach((to, from, next) => {
  store.commit('updateLoadStatus', false);

  // 登录跳转
  if (!store.state.xAuthToken && to.name !== 'index') {
    return next({name: 'index'});
  }
  if (store.state.xAuthToken && to.name === 'index') {
    return next({name: 'intro'});
  }

  return next();
});

router.afterEach((to, from) => {
});

export default router
