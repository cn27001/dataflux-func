(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-a87d2faa"],{"0797":function(t,e){t.exports=function(t){t.options.__i18n=t.options.__i18n||[],t.options.__i18n.push('{"zh-CN":{"Download as text file":"作为文本文件下载"}}'),delete t.options._Ctor}},"21a6":function(t,e,a){t.exports=a("407a")(1568)},"2f37":function(t,e){t.exports=function(t){t.options.__i18n=t.options.__i18n||[],t.options.__i18n.push('{"zh-CN":{"Time":"时间","User":"用户","User ID":"用户ID","IP Address":"IP地址","Operation":"操作","Data ID":"数据ID","MODIFY":"修改操作","DELETE":"删除操作","Cost":"耗时","ms":"毫秒","Show detail":"显示请求详情","The full content is following":"完整内容如下","Request":"请求","Response":"响应","Search Operation Record, User(ID, username), Client ID, Trace ID":"搜索操作记录，用户（ID、用户名），客户端ID，跟踪ID"}}'),delete t.options._Ctor}},"48bd":function(t,e,a){"use strict";var o=a("2f37"),n=a.n(o);e["default"]=n.a},"4b38":function(t,e,a){"use strict";a.r(e);var o=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("transition",{attrs:{name:"fade"}},[t.$store.state.isLoaded?a("el-container",{attrs:{direction:"vertical"}},[a("el-header",{attrs:{height:"60px"}},[a("h1",[t._v("\n        近期操作记录\n        "),a("div",{staticClass:"header-control"},[a("FuzzySearchInput",{attrs:{dataFilter:t.dataFilter,searchTip:t.$t("Search Operation Record, User(ID, username), Client ID, Trace ID")}})],1)])]),t._v(" "),a("el-main",{staticClass:"common-table-container"},[t.T.isNothing(t.data)?a("div",{staticClass:"no-data-area"},[t.T.isPageFiltered()?a("h1",{staticClass:"no-data-title"},[t._v("当前过滤条件无匹配数据")]):a("h1",{staticClass:"no-data-title"},[t._v("尚无任何近期操作记录")]),t._v(" "),a("p",{staticClass:"no-data-tip"},[t._v("\n          所有重要的操作会被系统搜集，并展示在此\n        ")])]):a("el-table",{staticClass:"common-table",attrs:{height:"100%",data:t.data,"row-class-name":t.highlightRow}},[a("el-table-column",{attrs:{label:t.$t("Time"),width:"200"},scopedSlots:t._u([{key:"default",fn:function(e){return[a("span",[t._v(t._s(t._f("datetime")(e.row.createTime)))]),t._v(" "),a("br"),t._v(" "),a("span",{staticClass:"text-info"},[t._v(t._s(t._f("fromNow")(e.row.createTime)))])]}}],null,!1,273918412)}),t._v(" "),a("el-table-column",{attrs:{label:t.$t("User"),width:"240"},scopedSlots:t._u([{key:"default",fn:function(e){return[a("strong",[t._v(t._s(e.row.u_name||t.$t("Anonymity")))]),t._v(" "),e.row.userId?[a("br"),t._v(" "),a("span",{staticClass:"text-info"},[t._v(t._s(t.$t("User ID"))+t._s(t.$t(":")))]),t._v(" "),a("code",{staticClass:"text-code text-small"},[t._v(t._s(e.row.userId))]),a("CopyButton",{attrs:{content:e.row.userId}})]:t._e(),t._v(" "),t.T.isNothing(e.row.clientIPsJSON)?t._e():[a("br"),t._v(" "),a("span",{staticClass:"text-info"},[t._v(t._s(t.$t("IP Address"))+t._s(t.$t(":")))]),t._v(" "),a("code",{staticClass:"text-code text-small"},[t._v(t._s(e.row.clientIPsJSON.join(", ")))]),a("CopyButton",{attrs:{content:e.row.clientIPsJSON.join(", ")}})]]}}],null,!1,161199714)}),t._v(" "),a("el-table-column",{attrs:{label:t.$t("Operation")},scopedSlots:t._u([{key:"default",fn:function(e){return[e.row.respStatusCode>=200&&e.row.respStatusCode<400?a("span",{staticClass:"text-good"},[a("i",{staticClass:"fa fa-fw fa-check-circle"})]):a("span",{staticClass:"text-bad"},[a("i",{staticClass:"fa fa-fw fa-times-circle"})]),t._v(" "),a("span",[t._v(t._s(e.row.reqRouteName))]),t._v(" "),t.T.endsWith(e.row.reqRoute,"/do/modify")?a("strong",{staticClass:"text-watch"},[t._v("\n              （"+t._s(t.$t("MODIFY"))+"）\n            ")]):t._e(),t._v(" "),t.T.endsWith(e.row.reqRoute,"/do/delete")?a("strong",{staticClass:"text-bad"},[t._v("\n              （"+t._s(t.$t("DELETE"))+"）\n            ")]):t._e(),t._v(" "),e.row._operationEntityId?[a("br"),t._v(" "),a("span",{staticClass:"text-info"},[t._v(t._s(t.$t("Data ID"))+t._s(t.$t(":")))]),t._v(" "),a("code",{staticClass:"text-code text-small"},[t._v(t._s(e.row._operationEntityId))]),a("CopyButton",{attrs:{content:e.row._operationEntityId}})]:t._e()]}}],null,!1,3632919402)}),t._v(" "),a("el-table-column",{attrs:{label:t.$t("Cost"),align:"right",width:"100"},scopedSlots:t._u([{key:"default",fn:function(e){return[t._v("\n            "+t._s(e.row.reqCost)+" "),a("span",{staticClass:"text-info"},[t._v(t._s(t.$t("ms")))])]}}],null,!1,409322375)}),t._v(" "),a("el-table-column",{attrs:{align:"right",width:"150"},scopedSlots:t._u([{key:"default",fn:function(e){return[a("el-button",{attrs:{type:"text"},on:{click:function(a){return t.showDetail(e.row)}}},[t._v(t._s(t.$t("Show detail")))])]}}],null,!1,3868636333)})],1)],1),t._v(" "),a("Pager",{attrs:{pageInfo:t.pageInfo}}),t._v(" "),a("LongTextDialog",{ref:"longTextDialog",attrs:{title:t.$t("The full content is following"),showDownload:!0}})],1):t._e()],1)},n=[],s=a("1da1"),r=(a("99af"),a("e9c4"),a("a15b"),a("96cf"),a("b76c")),i={name:"OperationRecordList",components:{LongTextDialog:r["a"]},watch:{$route:{immediate:!0,handler:function(t,e){var a=this;return Object(s["a"])(regeneratorRuntime.mark((function t(){return regeneratorRuntime.wrap((function(t){while(1)switch(t.prev=t.next){case 0:return t.next=2,a.loadData();case 2:case"end":return t.stop()}}),t)})))()}}},methods:{highlightRow:function(t){var e=t.row;t.rowIndex;return this.$store.state.highlightedTableDataId===e.id?"hl-row":""},loadData:function(){var t=this;return Object(s["a"])(regeneratorRuntime.mark((function e(){var a;return regeneratorRuntime.wrap((function(e){while(1)switch(e.prev=e.next){case 0:return e.next=2,t.T.callAPI_get("/api/v1/operation-records/do/list",{query:t.T.createListQuery()});case 2:if(a=e.sent,a.ok){e.next=5;break}return e.abrupt("return");case 5:t.data=a.data,t.pageInfo=a.pageInfo,t.$store.commit("updateLoadStatus",!0);case 8:case"end":return e.stop()}}),e)})))()},showDetail:function(t){this.$store.commit("updateHighlightedTableDataId",t.id);var e=[];e.push("===== ".concat(this.$t("Request")," =====")),e.push("".concat(t.reqMethod.toUpperCase()," ").concat(this.T.formatURL(t.reqRoute,{params:t.reqParamsJSON,query:t.reqQueryJSON}))),t.reqBodyJSON&&e.push(JSON.stringify(t.reqBodyJSON,null,2)),e.push("\n===== ".concat(this.$t("Response")," =====")),e.push("Status Code: ".concat(t.respStatusCode)),t.respBodyJSON&&e.push(JSON.stringify(t.respBodyJSON,null,2));var a=e.join("\n"),o=this.M(t.createTime).utcOffset(8).format("YYYYMMDD_HHmmss"),n="http-dump.".concat(o);this.$refs.longTextDialog.update(a,n)}},computed:{},props:{},data:function(){var t=this.T.createPageInfo(),e=this.T.createListQuery();return{data:[],pageInfo:t,dataFilter:{_fuzzySearch:e._fuzzySearch}}}},l=i,c=a("2877"),u=a("48bd"),d=Object(c["a"])(l,o,n,!1,null,"68072cdb",null);"function"===typeof u["default"]&&Object(u["default"])(d);e["default"]=d.exports},"7b0b":function(t,e,a){"use strict";var o=a("0797"),n=a.n(o);e["default"]=n.a},a7e8:function(t,e,a){"use strict";a("b217")},b217:function(t,e,a){},b76c:function(t,e,a){"use strict";var o=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("el-dialog",{attrs:{id:"LongTextDialog",visible:t.show,width:"70%"},on:{"update:visible":function(e){t.show=e}}},[a("template",{slot:"title"},[t.showDownload&&t.fileName&&t.content?a("el-link",{attrs:{type:"primary"},on:{click:t.download}},[t._v("\n      "+t._s(t.$t("Download as text file"))+"\n      "),a("i",{staticClass:"fa fa-fw fa-download"})]):t._e()],1),t._v(" "),a("div",[a("p",[t._v(t._s(t.title))]),t._v(" "),a("textarea",{attrs:{id:"longTextDialogContent"}})])],2)},n=[],s=(a("130f"),a("21a6")),r=a.n(s),i={name:"LongTextDialog",components:{},watch:{},methods:{update:function(t,e){var a=this;this.codeMirror&&this.codeMirror.setValue(""),this.content=t,this.fileName=(e||"dump")+".txt",this.show=!0,setImmediate((function(){a.codeMirror||(a.codeMirror=a.T.initCodeMirror("longTextDialogContent",a.mode||"text"),a.codeMirror.setOption("theme",a.T.getCodeMirrorThemeName()),a.T.setCodeMirrorReadOnly(a.codeMirror,!0)),a.codeMirror.setValue(a.content||""),a.codeMirror.refresh()}))},download:function(){var t=new Blob([this.content],{type:"text/plain"}),e=this.fileName;r.a.saveAs(t,e)}},computed:{},props:{title:String,mode:Boolean,showDownload:Boolean},data:function(){return{show:!1,fileName:null,content:null,codeMirror:null}},beforeDestroy:function(){this.T.destoryCodeMirror(this.codeMirror)}},l=i,c=(a("a7e8"),a("2877")),u=a("7b0b"),d=Object(c["a"])(l,o,n,!1,null,"ece94f2e",null);"function"===typeof u["default"]&&Object(u["default"])(d);e["a"]=d.exports}}]);