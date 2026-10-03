// src/styles.css
var styles_default = '.osp-root {\n  --osp-bg: #191d21;\n  --osp-panel: #21262b;\n  --osp-line: #374048;\n  --osp-text: #edf1f4;\n  --osp-muted: #a8b2bc;\n  --osp-accent: #a4e5d6;\n  color: var(--osp-text);\n  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;\n  font-size: 14px;\n  line-height: 1.5;\n  max-width: 1320px;\n  margin: 0 auto;\n  padding: 34px 30px 26px;\n  color-scheme: dark;\n}\n.osp-root * { box-sizing: border-box; }\n.osp-root h1, .osp-root h2, .osp-root h3, .osp-root p { margin: 0; }\n.osp-root h1 { font-size: 29px; line-height: 1.25; letter-spacing: -.6px; font-weight: 650; }\n.osp-root h2 { font-size: 19px; line-height: 1.4; overflow-wrap: anywhere; font-weight: 600; }\n.osp-root h3 { font-size: 14px; }\n.osp-root .osp-header { display: flex; justify-content: space-between; align-items: center; gap: 24px; margin-bottom: 26px; }\n.osp-root .osp-eyebrow { color: var(--osp-accent); font-size: 10px; font-weight: 650; letter-spacing: 1.4px; text-transform: uppercase; margin-bottom: 7px; }\n.osp-root .osp-subtitle { color: var(--osp-muted); margin-top: 8px; }\n.osp-root .osp-actions { display: flex; align-items: center; gap: 14px; flex-shrink: 0; }\n.osp-root .osp-readonly { color: var(--osp-muted); font-size: 12px; white-space: nowrap; }\n.osp-root .osp-readonly::before { content: ""; display: inline-block; height: 6px; width: 6px; background: var(--osp-accent); border-radius: 50%; margin-right: 7px; }\n.osp-root .osp-button { border: 1px solid var(--osp-line); border-radius: 7px; padding: 9px 15px; background: var(--osp-panel); color: var(--osp-text); font: inherit; font-size: 13px; font-weight: 550; cursor: pointer; white-space: nowrap; }\n.osp-root .osp-button:hover:not(:disabled) { background: #30383f; border-color: #65737e; }\n.osp-root .osp-primary { background: var(--osp-accent); color: #142d28; border-color: var(--osp-accent); }\n.osp-root .osp-primary:hover:not(:disabled) { background: #c0f1e5; border-color: #c0f1e5; }\n.osp-root .osp-button:disabled { cursor: wait; opacity: .55; }\n.osp-root :is(button, input, a):focus-visible { outline: 2px solid var(--osp-accent); outline-offset: 4px; }\n.osp-root .osp-project { display: flex; align-items: flex-end; gap: 10px; padding: 16px 18px; background: var(--osp-bg); border: 1px solid var(--osp-line); border-radius: 9px; }\n.osp-root .osp-field { flex: 1; min-width: 0; }\n.osp-root .osp-label { display: block; color: var(--osp-muted); font-size: 11px; font-weight: 550; letter-spacing: .3px; margin-bottom: 6px; }\n.osp-root input { width: 100%; border: 1px solid var(--osp-line); border-radius: 5px; padding: 9px 11px; background: #14181c; color: var(--osp-text); font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; }\n.osp-root input:disabled { opacity: .7; }\n.osp-root .osp-notice { padding: 11px 0; font-size: 11px; color: var(--osp-muted); overflow-wrap: anywhere; min-height: 40px; }\n.osp-root .osp-error { border: 1px solid #80564b; background: #352924; border-radius: 7px; padding: 13px 15px; color: #f1c6b9; margin: 10px 0; overflow-wrap: anywhere; }\n.osp-root .osp-metrics { display: grid; grid-template-columns: repeat(3, 1fr); border-block: 1px solid var(--osp-line); padding: 19px 0; margin: 6px 0 28px; }\n.osp-root .osp-metric { padding: 0 24px; border-left: 1px solid var(--osp-line); }\n.osp-root .osp-metric:first-child { padding-left: 0; border: 0; }\n.osp-root .osp-metric strong { display: block; font-size: 28px; line-height: 1.4; letter-spacing: -.6px; font-weight: 600; }\n.osp-root .osp-metric .osp-muted { font-size: 11px; }\n.osp-root .osp-muted { color: var(--osp-muted); }\n.osp-root .osp-columns { display: grid; grid-template-columns: minmax(220px, .8fr) minmax(0, 1.8fr); gap: 24px; }\n.osp-root .osp-panel-title { margin-bottom: 13px; font-size: 13px; color: var(--osp-muted); }\n.osp-root .osp-change-list, .osp-root .osp-artifacts, .osp-root .osp-tasks { list-style: none; padding: 0; margin: 0; }\n.osp-root .osp-change-list { display: flex; flex-direction: column; gap: 10px; }\n.osp-root .osp-change { display: block; text-decoration: none; color: var(--osp-text); border: 1px solid var(--osp-line); border-radius: 8px; padding: 16px; background: var(--osp-bg); }\n.osp-root .osp-change:hover { border-color: #72818c; background: var(--osp-panel); }\n.osp-root .osp-selected { border-color: #80bbae; background: #202f2e; box-shadow: inset 3px 0 0 var(--osp-accent); }\n.osp-root .osp-change-name { display: block; font-size: 13px; font-weight: 600; overflow-wrap: anywhere; margin-bottom: 5px; }\n.osp-root .osp-change .osp-muted { display: block; font-size: 11px; }\n.osp-root .osp-progress { overflow: hidden; height: 4px; background: #3a4249; border-radius: 2px; margin: 13px 0 10px; }\n.osp-root .osp-progress span { display: block; height: 100%; background: var(--osp-accent); }\n.osp-root .osp-date { display: block; font-size: 10px; color: var(--osp-muted); margin-top: 4px; }\n.osp-root .osp-detail { border: 1px solid var(--osp-line); border-radius: 10px; padding: 22px; background: var(--osp-bg); min-width: 0; }\n.osp-root .osp-detail-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; padding-bottom: 20px; border-bottom: 1px solid var(--osp-line); }\n.osp-root .osp-section-title { margin: 20px 0 12px; font-size: 12px; font-weight: 550; color: var(--osp-muted); }\n.osp-root .osp-artifacts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }\n.osp-root .osp-artifact { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; padding: 11px; border: 1px solid var(--osp-line); border-radius: 6px; background: var(--osp-panel); }\n.osp-root .osp-artifact strong { font-size: 12px; font-weight: 550; text-transform: capitalize; }\n.osp-root .osp-artifact-path { display: block; color: var(--osp-muted); font: 10px/1.5 ui-monospace, monospace; overflow-wrap: anywhere; margin-top: 3px; }\n.osp-root .osp-badge { display: inline-block; flex-shrink: 0; border: 1px solid #536270; border-radius: 20px; padding: 2px 8px; font-size: 10px; white-space: nowrap; color: var(--osp-muted); }\n.osp-root .osp-done { color: #b2ebdc; background: #223b34; border-color: #405e55; }\n.osp-root .osp-ready { color: #e8d7a5; background: #393425; border-color: #686044; }\n.osp-root .osp-blocked { color: #ebc2b4; background: #392a28; border-color: #74534d; }\n.osp-root .osp-task-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }\n.osp-root .osp-task-header .osp-muted { font-size: 11px; }\n.osp-root .osp-task { display: flex; gap: 10px; padding: 11px 0; border-bottom: 1px solid #30383e; font-size: 12px; }\n.osp-root .osp-task:last-child { border-bottom: 0; }\n.osp-root .osp-check { flex: 0 0 17px; color: var(--osp-muted); font-size: 14px; }\n.osp-root .osp-checked { color: var(--osp-accent); }\n.osp-root .osp-task-source { display: block; font: 10px/1.5 ui-monospace, monospace; color: #82909b; overflow-wrap: anywhere; margin-top: 4px; }\n.osp-root .osp-next { border-top: 1px solid var(--osp-line); margin-top: 22px; padding-top: 16px; font-size: 12px; }\n.osp-root .osp-next strong { color: var(--osp-accent); font-size: 11px; font-weight: 550; }\n.osp-root .osp-next p { color: var(--osp-muted); margin-top: 5px; }\n.osp-root .osp-empty { color: var(--osp-muted); padding: 18px 0; line-height: 1.7; }\n.osp-root .osp-footer { color: #929da7; font-size: 11px; margin-top: 24px; padding-top: 15px; border-top: 1px solid var(--osp-line); }\n@media (max-width: 1050px) {\n  .osp-root { padding: 24px 18px; }\n  .osp-root .osp-columns { grid-template-columns: minmax(190px, .8fr) minmax(0, 1.4fr); gap: 16px; }\n  .osp-root .osp-artifacts { grid-template-columns: 1fr; }\n  .osp-root .osp-detail-header { display: block; }\n  .osp-root .osp-detail-header .osp-badge { margin-top: 10px; }\n}\n@media (max-width: 720px) {\n  .osp-root { padding: 20px 12px; }\n  .osp-root .osp-header { align-items: flex-start; flex-direction: column; gap: 16px; }\n  .osp-root h1 { font-size: 25px; }\n  .osp-root .osp-project { flex-wrap: wrap; padding: 12px; }\n  .osp-root .osp-field { flex-basis: 100%; }\n  .osp-root .osp-metric { padding: 0 12px; }\n  .osp-root .osp-metric strong { font-size: 23px; }\n  .osp-root .osp-columns { grid-template-columns: 1fr; }\n  .osp-root .osp-detail { padding: 17px; }\n}\n';

// embedded-raw-source:/Users/oka/Desktop/openhands-automation/apps/openspec-progress/src/collector.cjs
var collector_default = new TextDecoder().decode(Uint8Array.from(atob("J3VzZSBzdHJpY3QnOwoKLy8gUmVhZC1vbmx5IGNvbGxlY3RvciBlbWJlZGRlZCBpbiB0aGUgQXBwIGFuZCBleGVjdXRlZCBieSB0aGUgbG9jYWwgQWdlbnQgU2VydmVyLgpjb25zdCB7IGV4ZWNGaWxlIH0gPSByZXF1aXJlKCdub2RlOmNoaWxkX3Byb2Nlc3MnKTsKY29uc3QgeyByZWFscGF0aFN5bmMgfSA9IHJlcXVpcmUoJ25vZGU6ZnMnKTsKY29uc3QgcGF0aCA9IHJlcXVpcmUoJ25vZGU6cGF0aCcpOwpjb25zdCB7IHByb21pc2lmeSB9ID0gcmVxdWlyZSgnbm9kZTp1dGlsJyk7Cgpjb25zdCBNQVhfT1VUUFVUID0gMTI4ICogMTAyNDsKY29uc3QgTUFYX0NMSV9PVVRQVVQgPSA1MTIgKiAxMDI0Owpjb25zdCBTTFVHID0gL15bYS16MC05XSsoPzotW2EtejAtOV0rKSokLzsKY29uc3QgZXhlY3V0ZSA9IHByb21pc2lmeShleGVjRmlsZSk7CgpjbGFzcyBDb2xsZWN0b3JFcnJvciBleHRlbmRzIEVycm9yIHt9CgpmdW5jdGlvbiByZXF1aXJlVmFsdWUoY29uZGl0aW9uLCBtZXNzYWdlKSB7CiAgaWYgKCFjb25kaXRpb24pIHRocm93IG5ldyBDb2xsZWN0b3JFcnJvcihtZXNzYWdlKTsKfQoKZnVuY3Rpb24gb2JqZWN0KHZhbHVlKSB7CiAgcmV0dXJuIHZhbHVlICE9PSBudWxsICYmIHR5cGVvZiB2YWx1ZSA9PT0gJ29iamVjdCcgJiYgIUFycmF5LmlzQXJyYXkodmFsdWUpOwp9CgpmdW5jdGlvbiB0ZXh0KHZhbHVlLCBsaW1pdCA9IDIwMDApIHsKICByZXR1cm4gdHlwZW9mIHZhbHVlID09PSAnc3RyaW5nJyAmJiB2YWx1ZS5sZW5ndGggPiAwICYmIHZhbHVlLmxlbmd0aCA8PSBsaW1pdCAmJiAhdmFsdWUuaW5jbHVkZXMoJ1wwJyk7Cn0KCmZ1bmN0aW9uIHNsdWcodmFsdWUpIHsKICByZXR1cm4gdGV4dCh2YWx1ZSwgMTAwKSAmJiBTTFVHLnRlc3QodmFsdWUpOwp9CgpmdW5jdGlvbiBjb3VudCh2YWx1ZSkgewogIHJldHVybiBOdW1iZXIuaXNTYWZlSW50ZWdlcih2YWx1ZSkgJiYgdmFsdWUgPj0gMDsKfQoKZnVuY3Rpb24gdW5pcXVlKHZhbHVlcywgbWVzc2FnZSkgewogIHJlcXVpcmVWYWx1ZShuZXcgU2V0KHZhbHVlcykuc2l6ZSA9PT0gdmFsdWVzLmxlbmd0aCwgbWVzc2FnZSk7Cn0KCmZ1bmN0aW9uIHZhbGlkYXRlSW5wdXQoaW5wdXQpIHsKICByZXF1aXJlVmFsdWUob2JqZWN0KGlucHV0KSwgJ0lucHV0IG11c3QgYmUgYW4gb2JqZWN0LicpOwogIHJlcXVpcmVWYWx1ZShPYmplY3Qua2V5cyhpbnB1dCkuZXZlcnkoa2V5ID0+IFsnYWN0aW9uJywgJ2NoYW5nZSddLmluY2x1ZGVzKGtleSkpLCAnVW5zdXBwb3J0ZWQgaW5wdXQgZmllbGQuJyk7CiAgcmVxdWlyZVZhbHVlKGlucHV0LmFjdGlvbiA9PT0gJ292ZXJ2aWV3JyB8fCBpbnB1dC5hY3Rpb24gPT09ICdjaGFuZ2UnLCAnVW5zdXBwb3J0ZWQgYWN0aW9uLicpOwogIGlmIChpbnB1dC5hY3Rpb24gPT09ICdvdmVydmlldycpIHsKICAgIHJlcXVpcmVWYWx1ZSghT2JqZWN0Lmhhc093bihpbnB1dCwgJ2NoYW5nZScpLCAnT3ZlcnZpZXcgZG9lcyBub3QgYWNjZXB0IGEgY2hhbmdlIG5hbWUuJyk7CiAgfSBlbHNlIHsKICAgIHJlcXVpcmVWYWx1ZShzbHVnKGlucHV0LmNoYW5nZSksICdDaGFuZ2UgbXVzdCBiZSBhIGtlYmFiLWNhc2UgbmFtZSBvZiBhdCBtb3N0IDEwMCBjaGFyYWN0ZXJzLicpOwogIH0KICByZXR1cm4gaW5wdXQ7Cn0KCmZ1bmN0aW9uIHZlcmlmeVJvb3QodmFsdWUsIHdvcmtzcGFjZSkgewogIHJlcXVpcmVWYWx1ZShvYmplY3QodmFsdWUpICYmIG9iamVjdCh2YWx1ZS5yb290KSAmJiB0eXBlb2YgdmFsdWUucm9vdC5wYXRoID09PSAnc3RyaW5nJywgJ09wZW5TcGVjIGRpZCBub3QgcmVwb3J0IGl0cyBwcm9qZWN0IHJvb3QuJyk7CiAgbGV0IHJvb3Q7CiAgdHJ5IHsgcm9vdCA9IHJlYWxwYXRoU3luYyh2YWx1ZS5yb290LnBhdGgpOyB9IGNhdGNoIHsgdGhyb3cgbmV3IENvbGxlY3RvckVycm9yKCdPcGVuU3BlYyByZXBvcnRlZCBhbiB1bmF2YWlsYWJsZSBwcm9qZWN0IHJvb3QuJyk7IH0KICByZXF1aXJlVmFsdWUocm9vdCA9PT0gd29ya3NwYWNlICYmIHBhdGgucmVzb2x2ZSh2YWx1ZS5yb290LnBhdGgpID09PSB3b3Jrc3BhY2UsCiAgICAnT3BlblNwZWMgcmVzb2x2ZWQgYSBkaWZmZXJlbnQgcHJvamVjdCByb290OyBzZWxlY3QgdGhlIGV4YWN0IGxvY2FsIHByb2plY3QgZGlyZWN0b3J5LicpOwp9Cgphc3luYyBmdW5jdGlvbiBjbGkoYXJncywgeyBydW4sIGN3ZCB9KSB7CiAgbGV0IHJlc3VsdDsKICB0cnkgewogICAgcmVzdWx0ID0gYXdhaXQgcnVuKCducHgnLCBbJy0tbm8taW5zdGFsbCcsICdvcGVuc3BlYycsIC4uLmFyZ3NdLCB7CiAgICAgIGN3ZCwgc2hlbGw6IGZhbHNlLCB0aW1lb3V0OiAxMl8wMDAsIG1heEJ1ZmZlcjogTUFYX0NMSV9PVVRQVVQsCiAgICAgIGVuY29kaW5nOiAndXRmOCcsIGVudjogeyAuLi5wcm9jZXNzLmVudiwgT1BFTlNQRUNfVEVMRU1FVFJZOiAnMCcgfSwKICAgIH0pOwogIH0gY2F0Y2ggKGVycm9yKSB7CiAgICBpZiAoZXJyb3I/LmtpbGxlZCB8fCBlcnJvcj8uY29kZSA9PT0gJ0VUSU1FRE9VVCcpIHRocm93IG5ldyBDb2xsZWN0b3JFcnJvcignT3BlblNwZWMgY29tbWFuZCB0aW1lZCBvdXQuJyk7CiAgICBpZiAoZXJyb3I/LmNvZGUgPT09ICdFUlJfQ0hJTERfUFJPQ0VTU19TVERJT19NQVhCVUZGRVInKSB0aHJvdyBuZXcgQ29sbGVjdG9yRXJyb3IoJ09wZW5TcGVjIGNvbW1hbmQgb3V0cHV0IGV4Y2VlZGVkIGl0cyBzaXplIGxpbWl0LicpOwogICAgdGhyb3cgbmV3IENvbGxlY3RvckVycm9yKCdPcGVuU3BlYyBjb21tYW5kIGZhaWxlZC4gQ2hlY2sgdGhhdCB0aGUgcHJvamVjdCBoYXMgYSBsb2NhbGx5IGluc3RhbGxlZCBPcGVuU3BlYyBDTEkuJyk7CiAgfQogIHJlcXVpcmVWYWx1ZShvYmplY3QocmVzdWx0KSAmJiB0eXBlb2YgcmVzdWx0LnN0ZG91dCA9PT0gJ3N0cmluZycsICdPcGVuU3BlYyBjb21tYW5kIHJldHVybmVkIG5vIEpTT04gb3V0cHV0LicpOwogIHJlcXVpcmVWYWx1ZShCdWZmZXIuYnl0ZUxlbmd0aChyZXN1bHQuc3Rkb3V0LCAndXRmOCcpIDw9IE1BWF9DTElfT1VUUFVULCAnT3BlblNwZWMgY29tbWFuZCBvdXRwdXQgZXhjZWVkZWQgaXRzIHNpemUgbGltaXQuJyk7CiAgbGV0IHZhbHVlOwogIHRyeSB7IHZhbHVlID0gSlNPTi5wYXJzZShyZXN1bHQuc3Rkb3V0KTsgfSBjYXRjaCB7IHRocm93IG5ldyBDb2xsZWN0b3JFcnJvcignT3BlblNwZWMgY29tbWFuZCByZXR1cm5lZCBtYWxmb3JtZWQgSlNPTi4nKTsgfQogIHZlcmlmeVJvb3QodmFsdWUsIGN3ZCk7CiAgcmV0dXJuIHZhbHVlOwp9CgpmdW5jdGlvbiBvdmVydmlldyh2YWx1ZSwgd29ya3NwYWNlKSB7CiAgcmVxdWlyZVZhbHVlKEFycmF5LmlzQXJyYXkodmFsdWUuY2hhbmdlcyksICdPcGVuU3BlYyByZXR1cm5lZCBhbiBpbnZhbGlkIGNoYW5nZSBsaXN0LicpOwogIGNvbnN0IGNoYW5nZXMgPSB2YWx1ZS5jaGFuZ2VzLm1hcChjaGFuZ2UgPT4gewogICAgcmVxdWlyZVZhbHVlKG9iamVjdChjaGFuZ2UpICYmIHNsdWcoY2hhbmdlLm5hbWUpLCAnT3BlblNwZWMgcmV0dXJuZWQgYW4gaW52YWxpZCBjaGFuZ2UgbmFtZS4nKTsKICAgIHJlcXVpcmVWYWx1ZShjb3VudChjaGFuZ2UuY29tcGxldGVkVGFza3MpICYmIGNvdW50KGNoYW5nZS50b3RhbFRhc2tzKSAmJiBjaGFuZ2UuY29tcGxldGVkVGFza3MgPD0gY2hhbmdlLnRvdGFsVGFza3MsCiAgICAgICdPcGVuU3BlYyByZXR1cm5lZCBpbnZhbGlkIHRhc2sgY291bnRzLicpOwogICAgcmVxdWlyZVZhbHVlKHRleHQoY2hhbmdlLmxhc3RNb2RpZmllZCwgMTAwKSAmJiBOdW1iZXIuaXNGaW5pdGUoRGF0ZS5wYXJzZShjaGFuZ2UubGFzdE1vZGlmaWVkKSksCiAgICAgICdPcGVuU3BlYyByZXR1cm5lZCBhbiBpbnZhbGlkIG1vZGlmaWNhdGlvbiB0aW1lLicpOwogICAgY29uc3QgZXhwZWN0ZWQgPSBjaGFuZ2UudG90YWxUYXNrcyA9PT0gMCA/ICduby10YXNrcycgOiBjaGFuZ2UuY29tcGxldGVkVGFza3MgPT09IGNoYW5nZS50b3RhbFRhc2tzID8gJ2NvbXBsZXRlJyA6ICdpbi1wcm9ncmVzcyc7CiAgICByZXF1aXJlVmFsdWUoY2hhbmdlLnN0YXR1cyA9PT0gZXhwZWN0ZWQsICdPcGVuU3BlYyByZXR1cm5lZCBhbiBpbmNvbnNpc3RlbnQgY2hhbmdlIHN0YXR1cy4nKTsKICAgIHJldHVybiB7IG5hbWU6IGNoYW5nZS5uYW1lLCBjb21wbGV0ZWRUYXNrczogY2hhbmdlLmNvbXBsZXRlZFRhc2tzLCB0b3RhbFRhc2tzOiBjaGFuZ2UudG90YWxUYXNrcywKICAgICAgbGFzdE1vZGlmaWVkOiBjaGFuZ2UubGFzdE1vZGlmaWVkLCBzdGF0dXM6IGNoYW5nZS5zdGF0dXMgfTsKICB9KTsKICB1bmlxdWUoY2hhbmdlcy5tYXAoY2hhbmdlID0+IGNoYW5nZS5uYW1lKSwgJ09wZW5TcGVjIHJldHVybmVkIGR1cGxpY2F0ZSBjaGFuZ2UgbmFtZXMuJyk7CiAgcmV0dXJuIHsgdmVyc2lvbjogMSwga2luZDogJ292ZXJ2aWV3Jywgd29ya3NwYWNlLCBnZW5lcmF0ZWRBdDogbmV3IERhdGUoKS50b0lTT1N0cmluZygpLCBjaGFuZ2VzIH07Cn0KCmZ1bmN0aW9uIHJlbGF0aXZlQXJ0aWZhY3RQYXRoKHZhbHVlKSB7CiAgcmV0dXJuIHRleHQodmFsdWUsIDIwMDApICYmICFwYXRoLmlzQWJzb2x1dGUodmFsdWUpICYmICF2YWx1ZS5pbmNsdWRlcygnXFwnKQogICAgJiYgIXZhbHVlLnNwbGl0KCcvJykuaW5jbHVkZXMoJy4uJyk7Cn0KCmZ1bmN0aW9uIHBsYW5uaW5nKHZhbHVlLCB3b3Jrc3BhY2UsIG5hbWUpIHsKICByZXF1aXJlVmFsdWUodmFsdWUuY2hhbmdlTmFtZSA9PT0gbmFtZSwgJ09wZW5TcGVjIHJldHVybmVkIGEgZGlmZmVyZW50IGNoYW5nZS4nKTsKICByZXF1aXJlVmFsdWUodGV4dCh2YWx1ZS5zY2hlbWFOYW1lLCAxMDApICYmIHR5cGVvZiB2YWx1ZS5pc1BsYW5uaW5nQ29tcGxldGUgPT09ICdib29sZWFuJyAmJiBBcnJheS5pc0FycmF5KHZhbHVlLmFydGlmYWN0cyksCiAgICAnT3BlblNwZWMgcmV0dXJuZWQgaW52YWxpZCBwbGFubmluZyBzdGF0dXMuJyk7CiAgY29uc3QgYXJ0aWZhY3RzID0gdmFsdWUuYXJ0aWZhY3RzLm1hcChhcnRpZmFjdCA9PiB7CiAgICByZXF1aXJlVmFsdWUob2JqZWN0KGFydGlmYWN0KSAmJiBzbHVnKGFydGlmYWN0LmlkKSAmJiByZWxhdGl2ZUFydGlmYWN0UGF0aChhcnRpZmFjdC5vdXRwdXRQYXRoKQogICAgICAmJiBbJ2RvbmUnLCAnc2tpcHBlZCcsICdyZWFkeScsICdibG9ja2VkJ10uaW5jbHVkZXMoYXJ0aWZhY3Quc3RhdHVzKQogICAgICAmJiBBcnJheS5pc0FycmF5KGFydGlmYWN0LnJlcXVpcmVzKSAmJiBhcnRpZmFjdC5yZXF1aXJlcy5ldmVyeShzbHVnKSwgJ09wZW5TcGVjIHJldHVybmVkIGFuIGludmFsaWQgcGxhbm5pbmcgYXJ0aWZhY3QuJyk7CiAgICB1bmlxdWUoYXJ0aWZhY3QucmVxdWlyZXMsICdPcGVuU3BlYyByZXR1cm5lZCBkdXBsaWNhdGUgYXJ0aWZhY3QgcmVxdWlyZW1lbnRzLicpOwogICAgcmV0dXJuIHsgaWQ6IGFydGlmYWN0LmlkLCBzdGF0dXM6IGFydGlmYWN0LnN0YXR1cywgb3V0cHV0UGF0aDogYXJ0aWZhY3Qub3V0cHV0UGF0aCwgcmVxdWlyZXM6IFsuLi5hcnRpZmFjdC5yZXF1aXJlc10gfTsKICB9KTsKICB1bmlxdWUoYXJ0aWZhY3RzLm1hcChhcnRpZmFjdCA9PiBhcnRpZmFjdC5pZCksICdPcGVuU3BlYyByZXR1cm5lZCBkdXBsaWNhdGUgcGxhbm5pbmcgYXJ0aWZhY3RzLicpOwogIHJldHVybiB7IHZlcnNpb246IDEsIGtpbmQ6ICdjaGFuZ2UnLCB3b3Jrc3BhY2UsIGdlbmVyYXRlZEF0OiBuZXcgRGF0ZSgpLnRvSVNPU3RyaW5nKCksIG5hbWUsCiAgICBzY2hlbWFOYW1lOiB2YWx1ZS5zY2hlbWFOYW1lLCBwbGFubmluZ0NvbXBsZXRlOiB2YWx1ZS5pc1BsYW5uaW5nQ29tcGxldGUsIGFydGlmYWN0cywKICAgIHByb2dyZXNzOiBudWxsLCB0YXNrczogW10sIGFwcGx5U3RhdGU6ICd1bmF2YWlsYWJsZScsIGluc3RydWN0aW9uOiAnJyB9Owp9CgpmdW5jdGlvbiB0YXNrRXZpZGVuY2UodmFsdWUsIGRldGFpbCkgewogIHJlcXVpcmVWYWx1ZSh2YWx1ZS5jaGFuZ2VOYW1lID09PSBkZXRhaWwubmFtZSAmJiB2YWx1ZS5zY2hlbWFOYW1lID09PSBkZXRhaWwuc2NoZW1hTmFtZSwgJ09wZW5TcGVjIHJldHVybmVkIGEgZGlmZmVyZW50IGNoYW5nZSBvciBzY2hlbWEuJyk7CiAgcmVxdWlyZVZhbHVlKFsnYmxvY2tlZCcsICdyZWFkeScsICdhbGxfZG9uZSddLmluY2x1ZGVzKHZhbHVlLnN0YXRlKSAmJiB0eXBlb2YgdmFsdWUuaW5zdHJ1Y3Rpb24gPT09ICdzdHJpbmcnCiAgICAmJiB0eXBlb2YgdmFsdWUudGFza1RyYWNraW5nQ29uZmlndXJlZCA9PT0gJ2Jvb2xlYW4nICYmIEFycmF5LmlzQXJyYXkodmFsdWUudGFza3MpLCAnT3BlblNwZWMgcmV0dXJuZWQgaW52YWxpZCBhcHBseSBpbnN0cnVjdGlvbnMuJyk7CiAgY29uc3QgcHJvZ3Jlc3MgPSB2YWx1ZS5wcm9ncmVzczsKICByZXF1aXJlVmFsdWUob2JqZWN0KHByb2dyZXNzKSAmJiBjb3VudChwcm9ncmVzcy50b3RhbCkgJiYgY291bnQocHJvZ3Jlc3MuY29tcGxldGUpICYmIGNvdW50KHByb2dyZXNzLnJlbWFpbmluZykKICAgICYmIHByb2dyZXNzLmNvbXBsZXRlIDw9IHByb2dyZXNzLnRvdGFsICYmIHByb2dyZXNzLnJlbWFpbmluZyA9PT0gcHJvZ3Jlc3MudG90YWwgLSBwcm9ncmVzcy5jb21wbGV0ZSwKICAnT3BlblNwZWMgcmV0dXJuZWQgaW52YWxpZCB0YXNrIHByb2dyZXNzLicpOwogIGNvbnN0IGNoYW5nZVJvb3QgPSBwYXRoLmpvaW4oZGV0YWlsLndvcmtzcGFjZSwgJ29wZW5zcGVjJywgJ2NoYW5nZXMnLCBkZXRhaWwubmFtZSk7CiAgY29uc3QgdGFza3MgPSB2YWx1ZS50YXNrcy5tYXAodGFzayA9PiB7CiAgICByZXF1aXJlVmFsdWUob2JqZWN0KHRhc2spICYmIHRleHQodGFzay5pZCwgMTAwKSAmJiB0ZXh0KHRhc2suZGVzY3JpcHRpb24sIE1BWF9PVVRQVVQpCiAgICAgICYmIHR5cGVvZiB0YXNrLmRvbmUgPT09ICdib29sZWFuJyAmJiB0ZXh0KHRhc2suc291cmNlUGF0aCwgMjAwMCkgJiYgcGF0aC5pc0Fic29sdXRlKHRhc2suc291cmNlUGF0aCkKICAgICAgJiYgcGF0aC5yZXNvbHZlKHRhc2suc291cmNlUGF0aCkuc3RhcnRzV2l0aChjaGFuZ2VSb290ICsgcGF0aC5zZXApCiAgICAgICYmIE51bWJlci5pc1NhZmVJbnRlZ2VyKHRhc2subGluZSkgJiYgdGFzay5saW5lID4gMCwgJ09wZW5TcGVjIHJldHVybmVkIGFuIGludmFsaWQgdGFzayBvciBzb3VyY2UgbG9jYXRpb24uJyk7CiAgICByZXR1cm4geyBpZDogdGFzay5pZCwgZGVzY3JpcHRpb246IHRhc2suZGVzY3JpcHRpb24sIGRvbmU6IHRhc2suZG9uZSwgc291cmNlUGF0aDogdGFzay5zb3VyY2VQYXRoLCBsaW5lOiB0YXNrLmxpbmUgfTsKICB9KTsKICB1bmlxdWUodGFza3MubWFwKHRhc2sgPT4gdGFzay5pZCksICdPcGVuU3BlYyByZXR1cm5lZCBkdXBsaWNhdGUgdGFzayBJRHMuJyk7CiAgcmVxdWlyZVZhbHVlKHRhc2tzLmxlbmd0aCA8PSBwcm9ncmVzcy50b3RhbCAmJiB0YXNrcy5maWx0ZXIodGFzayA9PiB0YXNrLmRvbmUpLmxlbmd0aCA8PSBwcm9ncmVzcy5jb21wbGV0ZQogICAgJiYgdGFza3MuZmlsdGVyKHRhc2sgPT4gIXRhc2suZG9uZSkubGVuZ3RoIDw9IHByb2dyZXNzLnJlbWFpbmluZywgJ09wZW5TcGVjIHRhc2sgZGVzY3JpcHRpb25zIGNvbnRyYWRpY3QgdGhlIHByb2dyZXNzIGNvdW50cy4nKTsKICByZXF1aXJlVmFsdWUodmFsdWUuc3RhdGUgIT09ICdhbGxfZG9uZScgfHwgKHByb2dyZXNzLnRvdGFsID4gMCAmJiBwcm9ncmVzcy5yZW1haW5pbmcgPT09IDApLCAnT3BlblNwZWMgcmV0dXJuZWQgYW4gaW5jb25zaXN0ZW50IGNvbXBsZXRpb24gc3RhdGUuJyk7CiAgZGV0YWlsLmFwcGx5U3RhdGUgPSB2YWx1ZS5zdGF0ZTsKICBkZXRhaWwuaW5zdHJ1Y3Rpb24gPSB2YWx1ZS5pbnN0cnVjdGlvbjsKICBkZXRhaWwudGFza3MgPSB0YXNrczsKICAvLyBBIHNjaGVtYSB3aXRob3V0IHRhc2sgdHJhY2tpbmcsIG9yIGEgYmxvY2tlZCBjaGFuZ2Ugd2l0aCBubyB0YXNrcyB5ZXQsCiAgLy8gaGFzIG5vIG1lYXN1cmFibGUgY29tcGxldGlvbiBwZXJjZW50YWdlLiBQcmVzZXJ2ZSB0aGF0IGRpc3RpbmN0aW9uLgogIGRldGFpbC5wcm9ncmVzcyA9ICF2YWx1ZS50YXNrVHJhY2tpbmdDb25maWd1cmVkIHx8ICh2YWx1ZS5zdGF0ZSA9PT0gJ2Jsb2NrZWQnICYmIHRhc2tzLmxlbmd0aCA9PT0gMCkKICAgID8gbnVsbCA6IHsgdG90YWw6IHByb2dyZXNzLnRvdGFsLCBjb21wbGV0ZTogcHJvZ3Jlc3MuY29tcGxldGUsIHJlbWFpbmluZzogcHJvZ3Jlc3MucmVtYWluaW5nIH07CiAgaWYgKEFycmF5LmlzQXJyYXkodmFsdWUudW5hdmFpbGFibGVUcmFja2luZ0ZpbGVzKSAmJiB2YWx1ZS51bmF2YWlsYWJsZVRyYWNraW5nRmlsZXMubGVuZ3RoKSB7CiAgICBkZXRhaWwucHJvZ3Jlc3MgPSBudWxsOwogICAgZGV0YWlsLnRhc2tFcnJvciA9ICdTb21lIHRhc2sgdHJhY2tpbmcgZmlsZXMgY291bGQgbm90IGJlIHJlYWQ7IGNvbXBsZXRpb24gaXMgbm90IHZlcmlmaWVkLic7CiAgfQogIHJldHVybiBkZXRhaWw7Cn0KCmZ1bmN0aW9uIGJvdW5kZWQodmFsdWUpIHsKICByZXF1aXJlVmFsdWUoQnVmZmVyLmJ5dGVMZW5ndGgoSlNPTi5zdHJpbmdpZnkodmFsdWUpLCAndXRmOCcpIDw9IE1BWF9PVVRQVVQsICdEYXNoYm9hcmQgZGF0YSBleGNlZWRlZCB0aGUgMTI4IEtpQiBvdXRwdXQgbGltaXQuJyk7CiAgcmV0dXJuIHZhbHVlOwp9CgpmdW5jdGlvbiBlcnJvclJlc3VsdChlcnJvcikgewogIHJldHVybiB7IHZlcnNpb246IDEsIGtpbmQ6ICdlcnJvcicsIG1lc3NhZ2U6IGVycm9yIGluc3RhbmNlb2YgQ29sbGVjdG9yRXJyb3IgPyBlcnJvci5tZXNzYWdlIDogJ0NvdWxkIG5vdCByZWFkIGxvY2FsIE9wZW5TcGVjIHByb2dyZXNzLicgfTsKfQoKYXN5bmMgZnVuY3Rpb24gY29sbGVjdChpbnB1dCwgeyBydW4gPSBleGVjdXRlLCBjd2QgPSBwcm9jZXNzLmN3ZCgpIH0gPSB7fSkgewogIHRyeSB7CiAgICB2YWxpZGF0ZUlucHV0KGlucHV0KTsKICAgIHJlcXVpcmVWYWx1ZSh0eXBlb2YgY3dkID09PSAnc3RyaW5nJyAmJiBwYXRoLmlzQWJzb2x1dGUoY3dkKSwgJ1dvcmtzcGFjZSBtdXN0IGJlIGFuIGFic29sdXRlIGxvY2FsIHBhdGguJyk7CiAgICBjb25zdCB3b3Jrc3BhY2UgPSByZWFscGF0aFN5bmMoY3dkKTsKICAgIGlmIChpbnB1dC5hY3Rpb24gPT09ICdvdmVydmlldycpIHJldHVybiBib3VuZGVkKG92ZXJ2aWV3KGF3YWl0IGNsaShbJ2xpc3QnLCAnLS1qc29uJ10sIHsgcnVuLCBjd2Q6IHdvcmtzcGFjZSB9KSwgd29ya3NwYWNlKSk7CiAgICBjb25zdCBkZXRhaWwgPSBwbGFubmluZyhhd2FpdCBjbGkoWydzdGF0dXMnLCAnLS1jaGFuZ2UnLCBpbnB1dC5jaGFuZ2UsICctLWpzb24nXSwgeyBydW4sIGN3ZDogd29ya3NwYWNlIH0pLCB3b3Jrc3BhY2UsIGlucHV0LmNoYW5nZSk7CiAgICB0cnkgewogICAgICB0YXNrRXZpZGVuY2UoYXdhaXQgY2xpKFsnaW5zdHJ1Y3Rpb25zJywgJ2FwcGx5JywgJy0tY2hhbmdlJywgaW5wdXQuY2hhbmdlLCAnLS1qc29uJ10sIHsgcnVuLCBjd2Q6IHdvcmtzcGFjZSB9KSwgZGV0YWlsKTsKICAgIH0gY2F0Y2ggKGVycm9yKSB7CiAgICAgIGRldGFpbC50YXNrRXJyb3IgPSBlcnJvclJlc3VsdChlcnJvcikubWVzc2FnZTsKICAgIH0KICAgIHJldHVybiBib3VuZGVkKGRldGFpbCk7CiAgfSBjYXRjaCAoZXJyb3IpIHsKICAgIHJldHVybiBlcnJvclJlc3VsdChlcnJvcik7CiAgfQp9Cgphc3luYyBmdW5jdGlvbiBtYWluKCkgewogIGxldCByZXN1bHQ7CiAgdHJ5IHsKICAgIGNvbnN0IGVuY29kZWQgPSBwcm9jZXNzLmFyZ3ZbMV07CiAgICByZXF1aXJlVmFsdWUodHlwZW9mIGVuY29kZWQgPT09ICdzdHJpbmcnICYmIGVuY29kZWQubGVuZ3RoID4gMCAmJiBlbmNvZGVkLmxlbmd0aCA8PSA4MTkyCiAgICAgICYmIC9eKD86W0EtWmEtejAtOSsvXXs0fSkqKD86W0EtWmEtejAtOSsvXXsyfT09fFtBLVphLXowLTkrL117M309KT8kLy50ZXN0KGVuY29kZWQpLCAnRXhwZWN0ZWQgb25lIGJhc2U2NC1lbmNvZGVkIEpTT04gaW5wdXQuJyk7CiAgICBjb25zdCBkZWNvZGVkID0gQnVmZmVyLmZyb20oZW5jb2RlZCwgJ2Jhc2U2NCcpOwogICAgcmVxdWlyZVZhbHVlKGRlY29kZWQubGVuZ3RoIDw9IDQwOTYgJiYgZGVjb2RlZC50b1N0cmluZygnYmFzZTY0JykgPT09IGVuY29kZWQsICdJbnB1dCBleGNlZWRlZCBpdHMgc2l6ZSBsaW1pdCBvciB3YXMgbm90IHZhbGlkIGJhc2U2NC4nKTsKICAgIGxldCBpbnB1dDsKICAgIHRyeSB7IGlucHV0ID0gSlNPTi5wYXJzZShkZWNvZGVkLnRvU3RyaW5nKCd1dGY4JykpOyB9IGNhdGNoIHsgdGhyb3cgbmV3IENvbGxlY3RvckVycm9yKCdJbnB1dCB3YXMgbm90IHZhbGlkIEpTT04uJyk7IH0KICAgIHJlc3VsdCA9IGF3YWl0IGNvbGxlY3QoaW5wdXQpOwogIH0gY2F0Y2ggKGVycm9yKSB7CiAgICByZXN1bHQgPSBlcnJvclJlc3VsdChlcnJvcik7CiAgfQogIHByb2Nlc3Muc3Rkb3V0LndyaXRlKEpTT04uc3RyaW5naWZ5KHJlc3VsdCkgKyAnXG4nKTsKICBpZiAocmVzdWx0LmtpbmQgPT09ICdlcnJvcicpIHByb2Nlc3MuZXhpdENvZGUgPSAxOwp9Cgptb2R1bGUuZXhwb3J0cyA9IHsgY29sbGVjdCB9OwppZiAoIW1vZHVsZS5wYXJlbnQpIG1haW4oKTsK"), (character) => character.charCodeAt(0)));

// src/client.js
var SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
var LIMIT = 128 * 1024;
function validateWorkspace(value) {
  if (typeof value !== "string" || !value.startsWith("/") || value.length > 4096 || /[\0\r\n]/.test(value)) {
    throw new Error("Enter an absolute project directory on the connected Agent Server.");
  }
  return value.replace(/\/+$/, "") || "/";
}
function count(value) {
  return Number.isSafeInteger(value) && value >= 0;
}
function object(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
function validateOverview(data) {
  if (!Array.isArray(data.changes) || data.changes.some((change) => !object(change) || typeof change.name !== "string" || !SLUG.test(change.name) || !count(change.totalTasks) || !count(change.completedTasks) || change.completedTasks > change.totalTasks || typeof change.lastModified !== "string") || new Set(data.changes.map((change) => change.name)).size !== data.changes.length) {
    throw new Error("OpenSpec returned an invalid change inventory.");
  }
}
function validateChange(data, name) {
  if (data.name !== name || typeof data.schemaName !== "string" || typeof data.planningComplete !== "boolean" || !Array.isArray(data.artifacts) || data.artifacts.some((item) => !object(item) || typeof item.id !== "string" || !["done", "ready", "blocked", "skipped"].includes(item.status) || typeof item.outputPath !== "string" || !Array.isArray(item.requires) || item.requires.some((id) => typeof id !== "string")) || !Array.isArray(data.tasks)) {
    throw new Error("OpenSpec returned invalid artifact or task data.");
  }
  if (data.tasks.some((task) => !object(task) || typeof task.id !== "string" || typeof task.description !== "string" || typeof task.done !== "boolean" || typeof task.sourcePath !== "string" || !Number.isSafeInteger(task.line) || task.line < 1)) {
    throw new Error("OpenSpec returned invalid task details.");
  }
  if (data.progress === null) return;
  const p = data.progress;
  if (!object(p) || !count(p.total) || !count(p.complete) || !count(p.remaining) || p.complete + p.remaining !== p.total || data.tasks.length > p.total || data.tasks.filter((task) => task.done).length > p.complete || data.tasks.filter((task) => !task.done).length > p.remaining) {
    throw new Error("OpenSpec returned inconsistent task counts.");
  }
}
async function query(host, workspace, input) {
  const cwd = validateWorkspace(workspace);
  const encoded = btoa(JSON.stringify(input));
  const quote = (value) => "'" + value.replaceAll("'", "'\\''") + "'";
  const command = `node -e ${quote(collector_default)} ${quote(encoded)}`;
  let response;
  try {
    response = await host.agentServer.request({
      method: "POST",
      path: "/api/bash/execute_bash_command",
      body: { command, cwd, timeout: 30 }
    });
  } catch {
    throw new Error("Cannot read OpenSpec from this Agent Server. Check its connection and project directory, then refresh.");
  }
  if (!object(response) || typeof response.stdout !== "string" || response.stdout.length > LIMIT || !Number.isInteger(response.order) || response.order !== 0 || !Number.isInteger(response.exit_code)) {
    throw new Error("The progress query did not return complete output. Try a smaller project or inspect the Agent Server.");
  }
  let data;
  try {
    data = JSON.parse(response.stdout);
  } catch {
    throw new Error("The progress query returned invalid output. Ensure Node.js and the project-pinned OpenSpec CLI are installed.");
  }
  if (object(data) && data.version === 1 && data.kind === "error" && typeof data.message === "string") {
    throw new Error(data.message.slice(0, 600));
  }
  if (response.exit_code !== 0 || !object(data) || data.version !== 1 || data.kind !== (input.action === "overview" ? "overview" : "change") || typeof data.workspace !== "string" || typeof data.generatedAt !== "string" || !Number.isFinite(Date.parse(data.generatedAt))) {
    throw new Error("OpenSpec progress could not be read reliably. Refresh to try again.");
  }
  if (input.action === "overview") validateOverview(data);
  else validateChange(data, input.change);
  return data;
}
function loadOverview(host, workspace) {
  return query(host, workspace, { action: "overview" });
}
function loadChange(host, workspace, change) {
  if (typeof change !== "string" || !SLUG.test(change)) throw new Error("Invalid OpenSpec change name.");
  return query(host, workspace, { action: "change", change });
}

// src/extension.js
var DEFAULT_WORKSPACE = "/Users/oka/Desktop/openHanda-demo";
var STATE_LABELS = { done: "Done", ready: "Ready to write", blocked: "Blocked", skipped: "Skipped" };
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== void 0) node.textContent = text;
  return node;
}
function button(text, className, handler) {
  const node = el("button", className, text);
  node.type = "button";
  node.addEventListener("click", handler);
  return node;
}
function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Unknown" : date.toLocaleString(void 0, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}
function progressBar(done, total, label) {
  const bar = el("div", "osp-progress");
  bar.setAttribute("role", "progressbar");
  bar.setAttribute("aria-label", label);
  bar.setAttribute("aria-valuemin", "0");
  bar.setAttribute("aria-valuemax", String(total || 1));
  bar.setAttribute("aria-valuenow", String(done));
  const fill = el("span");
  fill.style.width = `${total ? Math.round(done / total * 100) : 0}%`;
  bar.append(fill);
  return bar;
}
function activate(host) {
  if (host.apiVersion !== "1") throw new Error("OpenSpec progress requires Canvas host API 1.");
  const base = `/extensions/${encodeURIComponent(host.extension.name)}/progress`;
  const storageKey = `openhands.apps.openspec-progress:${host.backend.id}:workspace`;
  let remembered = DEFAULT_WORKSPACE;
  try {
    remembered = validateWorkspace(localStorage.getItem(storageKey) || DEFAULT_WORKSPACE);
  } catch {
  }
  const disposers = /* @__PURE__ */ new Set();
  const unregister = host.registerPage("progress", ({ container, path, navigate }) => {
    let disposed = false;
    let generation = 0;
    let workspace = remembered;
    let snapshot = null;
    let detail = null;
    let busy = false;
    const requested = path ? /^changes\/([a-z0-9]+(?:-[a-z0-9]+)*)$/.exec(path) : null;
    const root = el("section", "osp-root");
    const style = el("style");
    style.dataset.openspecProgress = "true";
    style.textContent = styles_default;
    root.append(style);
    container.append(root);
    function dispose() {
      disposed = true;
      generation++;
      root.remove();
      disposers.delete(dispose);
    }
    disposers.add(dispose);
    if (path && !requested) {
      root.append(
        el("h1", "", "Page not found"),
        el("p", "osp-muted", "This OpenSpec progress route is not available."),
        button("Back to progress", "osp-button", () => navigate(base))
      );
      return dispose;
    }
    if (host.backend.kind !== "local") {
      root.append(
        el("h1", "", "OpenSpec progress"),
        el("p", "osp-error", "Connect a supported Agent Server with a local OpenSpec workspace to view progress.")
      );
      return dispose;
    }
    const header = el("header", "osp-header");
    const heading = el("div");
    heading.append(
      el("p", "osp-eyebrow", "PROJECT WORKSPACE"),
      el("h1", "", "OpenSpec progress"),
      el("p", "osp-subtitle", "Planning artifacts and implementation checklists, directly from OpenSpec.")
    );
    const actions = el("div", "osp-actions");
    const refresh = button("Refresh", "osp-button osp-primary", () => refreshData());
    actions.append(el("span", "osp-readonly", "Read only"), refresh);
    header.append(heading, actions);
    const form = el("form", "osp-project");
    const label = el("label", "osp-field");
    label.append(el("span", "osp-label", "Project directory"));
    const input = el("input");
    input.type = "text";
    input.value = workspace;
    input.spellcheck = false;
    input.setAttribute("aria-label", "Project directory");
    input.autocomplete = "off";
    label.append(input);
    const load = el("button", "osp-button", "Load project");
    load.type = "submit";
    form.append(label, load);
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      if (busy) return;
      try {
        workspace = validateWorkspace(input.value.trim());
        remembered = workspace;
        try {
          localStorage.setItem(storageKey, workspace);
        } catch {
        }
        if (path) {
          navigate(base);
          return;
        }
        snapshot = null;
        detail = null;
        refreshData();
      } catch (error) {
        showError(error.message);
      }
    });
    const notice = el("div", "osp-notice");
    notice.setAttribute("role", "status");
    notice.setAttribute("aria-live", "polite");
    const metrics = el("div", "osp-metrics");
    const columns = el("div", "osp-columns");
    const changePanel = el("section", "osp-changes");
    const detailPanel = el("section", "osp-detail");
    detailPanel.setAttribute("aria-label", "Change details");
    columns.append(changePanel, detailPanel);
    const footer = el("footer", "osp-footer", "Task counts reflect OpenSpec checkboxes. They do not certify tests, review, or release readiness.");
    root.append(header, form, notice, metrics, columns, footer);
    function setBusy(value) {
      busy = value;
      refresh.disabled = value;
      load.disabled = value;
      input.disabled = value;
      refresh.textContent = value ? "Refreshing\u2026" : "Refresh";
      root.setAttribute("aria-busy", String(value));
    }
    function showError(message, prefix = "") {
      notice.className = "osp-notice osp-error";
      notice.setAttribute("role", "alert");
      notice.textContent = prefix + message;
    }
    function renderOverview(selected) {
      metrics.replaceChildren();
      const changes = snapshot.changes;
      const total = changes.reduce((sum, change) => sum + change.totalTasks, 0);
      const complete = changes.reduce((sum, change) => sum + change.completedTasks, 0);
      for (const [labelText, value, hint] of [
        ["Active changes", String(changes.length), "Not archived"],
        ["Tasks checked", `${complete} / ${total}`, total ? `${Math.round(complete / total * 100)}% of tracked tasks` : "No tracked tasks"],
        ["Remaining tasks", String(total - complete), "Across active changes"]
      ]) {
        const metric = el("div", "osp-metric");
        metric.append(el("span", "osp-label", labelText), el("strong", "", value), el("span", "osp-muted", hint));
        metrics.append(metric);
      }
      changePanel.replaceChildren(el("h2", "osp-panel-title", "Active changes"));
      if (!changes.length) {
        changePanel.append(el("p", "osp-empty", "No active changes. Create a proposal with your OpenSpec skill, then refresh."));
        return;
      }
      const list = el("ul", "osp-change-list");
      for (const change of changes) {
        const item = el("li");
        const link = el("a", `osp-change${selected === change.name ? " osp-selected" : ""}`);
        link.href = `${base}/changes/${encodeURIComponent(change.name)}`;
        if (selected === change.name) link.setAttribute("aria-current", "page");
        link.addEventListener("click", (event) => {
          event.preventDefault();
          navigate(link.getAttribute("href"));
        });
        const state = change.totalTasks === 0 ? "No tasks yet" : change.completedTasks === change.totalTasks ? "Tasks complete" : "In progress";
        link.append(
          el("strong", "osp-change-name", change.name),
          el("span", "osp-muted", `${change.completedTasks} of ${change.totalTasks} tasks \xB7 ${state}`),
          progressBar(change.completedTasks, change.totalTasks, `${change.name} task progress`),
          el("span", "osp-date", `Updated ${formatDate(change.lastModified)}`)
        );
        item.append(link);
        list.append(item);
      }
      changePanel.append(list);
    }
    function renderDetail() {
      detailPanel.replaceChildren();
      if (!detail) return;
      const head = el("div", "osp-detail-header");
      const title = el("div");
      title.append(el("p", "osp-eyebrow", detail.schemaName), el("h2", "", detail.name));
      head.append(title, el(
        "span",
        `osp-badge ${detail.planningComplete ? "osp-done" : "osp-ready"}`,
        detail.planningComplete ? "Planning complete" : "Planning in progress"
      ));
      detailPanel.append(head, el("h3", "osp-section-title", "Planning artifacts"));
      const artifacts = el("ol", "osp-artifacts");
      for (const artifact of detail.artifacts) {
        const item = el("li", "osp-artifact");
        const content = el("div");
        content.append(el("strong", "", artifact.id), el("code", "osp-artifact-path", artifact.outputPath));
        if (artifact.requires.length) content.append(el("span", "osp-date", `Requires ${artifact.requires.join(", ")}`));
        item.append(content, el("span", `osp-badge osp-${artifact.status}`, STATE_LABELS[artifact.status]));
        artifacts.append(item);
      }
      detailPanel.append(artifacts);
      const taskHeader = el("div", "osp-task-header");
      taskHeader.append(el("h3", "osp-section-title", "Implementation tasks"));
      if (detail.progress) taskHeader.append(el("span", "osp-muted", `${detail.progress.complete} / ${detail.progress.total} checked`));
      detailPanel.append(taskHeader);
      if (detail.progress === null) {
        detailPanel.append(el("p", "osp-empty", detail.taskError || detail.instruction || "Task progress is not available yet. Complete the planning artifacts first."));
      } else if (!detail.tasks.length) {
        detailPanel.append(el("p", "osp-empty", "No tasks are tracked for this change."));
      } else {
        if (detail.tasks.length < detail.progress.total) {
          detailPanel.append(el("p", "osp-muted", "Only available task descriptions are listed below."));
        }
        const tasks = el("ul", "osp-tasks");
        for (const task of detail.tasks) {
          const item = el("li", "osp-task");
          const mark = el("span", task.done ? "osp-check osp-checked" : "osp-check", task.done ? "\u2713" : "\u25CB");
          mark.setAttribute("aria-label", task.done ? "Complete" : "Remaining");
          const text = el("div");
          text.append(el("span", "", task.description));
          const relative = task.sourcePath.startsWith(snapshot.workspace + "/") ? task.sourcePath.slice(snapshot.workspace.length + 1) : task.sourcePath;
          text.append(el("code", "osp-task-source", `${relative}:${task.line}`));
          item.append(mark, text);
          tasks.append(item);
        }
        detailPanel.append(tasks);
      }
      const next = el("div", "osp-next");
      const nextText = !detail.planningComplete ? "Continue planning in an OpenHands conversation." : detail.progress === null ? "Resolve the task-tracking issue before starting implementation." : detail.progress.remaining ? "Continue Apply after reviewing the planning artifacts." : "Review implementation and verification evidence before syncing or archiving.";
      next.append(el("strong", "", "Next human decision"), el("p", "", nextText));
      detailPanel.append(next);
    }
    async function refreshData() {
      if (busy || disposed) return;
      const version = ++generation;
      const current = () => !disposed && version === generation;
      let overviewUpdated = false;
      setBusy(true);
      notice.className = "osp-notice";
      notice.setAttribute("role", "status");
      notice.textContent = snapshot ? "Refreshing the OpenSpec snapshot\u2026" : "Reading OpenSpec from the connected Agent Server\u2026";
      if (!snapshot) detailPanel.replaceChildren(el("p", "osp-empty", "Loading project progress\u2026"));
      try {
        const overview = await loadOverview(host, workspace);
        if (!current()) return;
        snapshot = overview;
        overviewUpdated = true;
        detail = null;
        const selected = requested?.[1] || overview.changes[0]?.name;
        renderOverview(selected);
        if (!selected) {
          detailPanel.replaceChildren(el("div", "osp-empty", "Your active change details will appear here."));
        } else if (!overview.changes.some((change) => change.name === selected)) {
          detailPanel.replaceChildren(
            el("h2", "", "Change not found"),
            el("p", "osp-empty", "This change may have been archived or removed. Choose another active change.")
          );
        } else {
          detailPanel.replaceChildren(el("p", "osp-empty", `Loading ${selected}\u2026`));
          try {
            const change = await loadChange(host, workspace, selected);
            if (!current()) return;
            detail = change;
            renderDetail();
          } catch (error) {
            if (!current()) return;
            detailPanel.replaceChildren(el("h2", "", selected), el("p", "osp-error", error.message));
            throw error;
          }
        }
        notice.textContent = `Snapshot updated ${formatDate(detail?.generatedAt || snapshot.generatedAt)} \xB7 ${snapshot.workspace}`;
      } catch (error) {
        if (current()) showError(error.message, overviewUpdated ? "Change details unavailable. " : snapshot ? "Refresh failed. Showing the previous snapshot. " : "");
      } finally {
        if (current()) setBusy(false);
      }
    }
    refreshData();
    return dispose;
  });
  return () => {
    for (const dispose of [...disposers]) dispose();
    unregister();
  };
}
export {
  activate
};
