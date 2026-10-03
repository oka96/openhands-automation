// src/styles.css
var styles_default = '.osp-root {\n  --osp-bg: #191d21;\n  --osp-panel: #21262b;\n  --osp-line: #374048;\n  --osp-text: #edf1f4;\n  --osp-muted: #a8b2bc;\n  --osp-accent: #a4e5d6;\n  color: var(--osp-text);\n  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;\n  font-size: 14px;\n  line-height: 1.5;\n  max-width: 1320px;\n  margin: 0 auto;\n  padding: 34px 30px 26px;\n  color-scheme: dark;\n}\n.osp-root * { box-sizing: border-box; }\n.osp-root h1, .osp-root h2, .osp-root h3, .osp-root p { margin: 0; }\n.osp-root h1 { font-size: 29px; line-height: 1.25; letter-spacing: -.6px; font-weight: 650; }\n.osp-root h2 { font-size: 19px; line-height: 1.4; overflow-wrap: anywhere; font-weight: 600; }\n.osp-root h3 { font-size: 14px; }\n.osp-root .osp-header { display: flex; justify-content: space-between; align-items: center; gap: 24px; margin-bottom: 26px; }\n.osp-root .osp-eyebrow { color: var(--osp-accent); font-size: 10px; font-weight: 650; letter-spacing: 1.4px; text-transform: uppercase; margin-bottom: 7px; }\n.osp-root .osp-subtitle { color: var(--osp-muted); margin-top: 8px; }\n.osp-root .osp-actions { display: flex; align-items: center; gap: 14px; flex-shrink: 0; }\n.osp-root .osp-readonly { color: var(--osp-muted); font-size: 12px; white-space: nowrap; }\n.osp-root .osp-readonly::before { content: ""; display: inline-block; height: 6px; width: 6px; background: var(--osp-accent); border-radius: 50%; margin-right: 7px; }\n.osp-root .osp-button { border: 1px solid var(--osp-line); border-radius: 7px; padding: 9px 15px; background: var(--osp-panel); color: var(--osp-text); font: inherit; font-size: 13px; font-weight: 550; cursor: pointer; white-space: nowrap; }\n.osp-root .osp-button:hover:not(:disabled) { background: #30383f; border-color: #65737e; }\n.osp-root .osp-primary { background: var(--osp-accent); color: #142d28; border-color: var(--osp-accent); }\n.osp-root .osp-primary:hover:not(:disabled) { background: #c0f1e5; border-color: #c0f1e5; }\n.osp-root .osp-button:disabled { cursor: wait; opacity: .55; }\n.osp-root :is(button, input, a):focus-visible { outline: 2px solid var(--osp-accent); outline-offset: 4px; }\n.osp-root .osp-project { display: flex; align-items: flex-end; gap: 10px; padding: 16px 18px; background: var(--osp-bg); border: 1px solid var(--osp-line); border-radius: 9px; }\n.osp-root .osp-field { flex: 1; min-width: 0; }\n.osp-root .osp-label { display: block; color: var(--osp-muted); font-size: 11px; font-weight: 550; letter-spacing: .3px; margin-bottom: 6px; }\n.osp-root input { width: 100%; border: 1px solid var(--osp-line); border-radius: 5px; padding: 9px 11px; background: #14181c; color: var(--osp-text); font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; }\n.osp-root input:disabled { opacity: .7; }\n.osp-root .osp-notice { padding: 11px 0; font-size: 11px; color: var(--osp-muted); overflow-wrap: anywhere; min-height: 40px; }\n.osp-root .osp-error { border: 1px solid #80564b; background: #352924; border-radius: 7px; padding: 13px 15px; color: #f1c6b9; margin: 10px 0; overflow-wrap: anywhere; }\n.osp-root .osp-metrics { display: grid; grid-template-columns: repeat(3, 1fr); border-block: 1px solid var(--osp-line); padding: 19px 0; margin: 6px 0 28px; }\n.osp-root .osp-metric { padding: 0 24px; border-left: 1px solid var(--osp-line); }\n.osp-root .osp-metric:first-child { padding-left: 0; border: 0; }\n.osp-root .osp-metric strong { display: block; font-size: 28px; line-height: 1.4; letter-spacing: -.6px; font-weight: 600; }\n.osp-root .osp-metric .osp-muted { font-size: 11px; }\n.osp-root .osp-muted { color: var(--osp-muted); }\n.osp-root .osp-columns { display: grid; grid-template-columns: minmax(220px, .8fr) minmax(0, 1.8fr); gap: 24px; }\n.osp-root .osp-panel-title { margin-bottom: 13px; font-size: 13px; color: var(--osp-muted); }\n.osp-root .osp-change-list, .osp-root .osp-artifacts, .osp-root .osp-tasks { list-style: none; padding: 0; margin: 0; }\n.osp-root .osp-change-list { display: flex; flex-direction: column; gap: 10px; }\n.osp-root .osp-change { display: block; text-decoration: none; color: var(--osp-text); border: 1px solid var(--osp-line); border-radius: 8px; padding: 16px; background: var(--osp-bg); }\n.osp-root .osp-change:hover { border-color: #72818c; background: var(--osp-panel); }\n.osp-root .osp-selected { border-color: #80bbae; background: #202f2e; box-shadow: inset 3px 0 0 var(--osp-accent); }\n.osp-root .osp-change-name { display: block; font-size: 13px; font-weight: 600; overflow-wrap: anywhere; margin-bottom: 5px; }\n.osp-root .osp-change .osp-muted { display: block; font-size: 11px; }\n.osp-root .osp-progress { overflow: hidden; height: 4px; background: #3a4249; border-radius: 2px; margin: 13px 0 10px; }\n.osp-root .osp-progress span { display: block; height: 100%; background: var(--osp-accent); }\n.osp-root .osp-date { display: block; font-size: 10px; color: var(--osp-muted); margin-top: 4px; }\n.osp-root .osp-detail { border: 1px solid var(--osp-line); border-radius: 10px; padding: 22px; background: var(--osp-bg); min-width: 0; }\n.osp-root .osp-detail-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; padding-bottom: 20px; border-bottom: 1px solid var(--osp-line); }\n.osp-root .osp-section-title { margin: 20px 0 12px; font-size: 12px; font-weight: 550; color: var(--osp-muted); }\n.osp-root .osp-artifacts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }\n.osp-root .osp-artifact { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; padding: 11px; border: 1px solid var(--osp-line); border-radius: 6px; background: var(--osp-panel); }\n.osp-root .osp-artifact strong { font-size: 12px; font-weight: 550; text-transform: capitalize; }\n.osp-root .osp-artifact-path { display: block; color: var(--osp-muted); font: 10px/1.5 ui-monospace, monospace; overflow-wrap: anywhere; margin-top: 3px; }\n.osp-root .osp-badge { display: inline-block; flex-shrink: 0; border: 1px solid #536270; border-radius: 20px; padding: 2px 8px; font-size: 10px; white-space: nowrap; color: var(--osp-muted); }\n.osp-root .osp-done { color: #b2ebdc; background: #223b34; border-color: #405e55; }\n.osp-root .osp-ready { color: #e8d7a5; background: #393425; border-color: #686044; }\n.osp-root .osp-blocked { color: #ebc2b4; background: #392a28; border-color: #74534d; }\n.osp-root .osp-task-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }\n.osp-root .osp-task-header .osp-muted { font-size: 11px; }\n.osp-root .osp-task { display: flex; gap: 10px; padding: 11px 0; border-bottom: 1px solid #30383e; font-size: 12px; }\n.osp-root .osp-task:last-child { border-bottom: 0; }\n.osp-root .osp-check { flex: 0 0 17px; color: var(--osp-muted); font-size: 14px; }\n.osp-root .osp-checked { color: var(--osp-accent); }\n.osp-root .osp-task-source { display: block; font: 10px/1.5 ui-monospace, monospace; color: #82909b; overflow-wrap: anywhere; margin-top: 4px; }\n.osp-root .osp-next { border-top: 1px solid var(--osp-line); margin-top: 22px; padding-top: 16px; font-size: 12px; }\n.osp-root .osp-next strong { color: var(--osp-accent); font-size: 11px; font-weight: 550; }\n.osp-root .osp-next p { color: var(--osp-muted); margin-top: 5px; }\n.osp-root .osp-empty { color: var(--osp-muted); padding: 18px 0; line-height: 1.7; }\n.osp-root .osp-footer { color: #929da7; font-size: 11px; margin-top: 24px; padding-top: 15px; border-top: 1px solid var(--osp-line); }\n.osp-root .osp-automation { border: 1px solid var(--osp-line); border-radius: 9px; margin: 4px 0 22px; background: var(--osp-bg); }\n.osp-root .osp-automation summary { cursor: pointer; padding: 15px 18px; font-weight: 550; }\n.osp-root .osp-automation summary:focus-visible { outline: 2px solid var(--osp-accent); outline-offset: 3px; }\n.osp-root .osp-automation-body { padding: 0 18px 18px; }\n.osp-root .osp-automation-connection { display: flex; justify-content: space-between; align-items: center; gap: 14px; margin: 16px 0 8px; }\n.osp-root .osp-explore-form { display: grid; gap: 14px; padding-top: 16px; }\n.osp-root textarea { display: block; width: 100%; resize: vertical; border: 1px solid var(--osp-line); border-radius: 5px; padding: 10px; background: #14181c; color: var(--osp-text); font: inherit; font-size: 12px; }\n.osp-root textarea:focus-visible { outline: 2px solid var(--osp-accent); outline-offset: 3px; }\n.osp-root .osp-disclosure { font-size: 11px; color: var(--osp-muted); line-height: 1.6; }\n.osp-root .osp-automation-result { margin-top: 12px; font-size: 12px; overflow-wrap: anywhere; }\n.osp-root .osp-run-link { display: inline-block; color: var(--osp-accent); margin-top: 8px; text-decoration: underline; }\n@media (max-width: 1050px) {\n  .osp-root { padding: 24px 18px; }\n  .osp-root .osp-columns { grid-template-columns: minmax(190px, .8fr) minmax(0, 1.4fr); gap: 16px; }\n  .osp-root .osp-artifacts { grid-template-columns: 1fr; }\n  .osp-root .osp-detail-header { display: block; }\n  .osp-root .osp-detail-header .osp-badge { margin-top: 10px; }\n}\n@media (max-width: 720px) {\n  .osp-root { padding: 20px 12px; }\n  .osp-root .osp-header { align-items: flex-start; flex-direction: column; gap: 16px; }\n  .osp-root h1 { font-size: 25px; }\n  .osp-root .osp-project { flex-wrap: wrap; padding: 12px; }\n  .osp-root .osp-field { flex-basis: 100%; }\n  .osp-root .osp-metric { padding: 0 12px; }\n  .osp-root .osp-metric strong { font-size: 23px; }\n  .osp-root .osp-columns { grid-template-columns: 1fr; }\n  .osp-root .osp-detail { padding: 17px; }\n}\n';

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
  const quote2 = (value) => "'" + value.replaceAll("'", "'\\''") + "'";
  const command = `node -e ${quote2(collector_default)} ${quote2(encoded)}`;
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

// embedded-raw-source:/Users/oka/Desktop/openhands-automation/apps/openspec-progress/src/automation_bridge.py
var automation_bridge_default = new TextDecoder().decode(Uint8Array.from(atob("IiIiRml4ZWQgbG9jYWwgYnJpZGdlIGZvciBleHBsaWNpdCwgcGFyYW1ldGVyaXplZCBFeHBsb3JlIGF1dG9tYXRpb24gcmVxdWVzdHMuCgpSdW5zIGluc2lkZSB0aGUgQWdlbnQgU2VydmVyLiBDcmVkZW50aWFscyBuZXZlciBsZWF2ZSB0aGlzIHByb2Nlc3MuIFRoZXJlIGlzIG5vCmxpc3RlbmVyIG9yIGRhZW1vbjogQ2FudmFzIGNhbGxzIHRoaXMgYm91bmRlZCBoZWxwZXIgdGhyb3VnaCBpdHMgQmFzaCBhZGFwdGVyLgoiIiIKaW1wb3J0IGJhc2U2NAppbXBvcnQgY29udGV4dGxpYgppbXBvcnQgZmNudGwKaW1wb3J0IGhhc2hsaWIKaW1wb3J0IGhtYWMKaW1wb3J0IGpzb24KaW1wb3J0IG9zCmZyb20gcGF0aGxpYiBpbXBvcnQgUGF0aAppbXBvcnQgcmUKaW1wb3J0IHNlY3JldHMKaW1wb3J0IHN5cwppbXBvcnQgdGVtcGZpbGUKaW1wb3J0IHVybGxpYi5lcnJvcgppbXBvcnQgdXJsbGliLnBhcnNlCmltcG9ydCB1cmxsaWIucmVxdWVzdAppbXBvcnQgdXVpZAoKU09VUkNFID0gIm9wZW5zcGVjLWRhc2hib2FyZCIKTkFNRSA9ICJPcGVuU3BlYyAwMSDCtyBFeHBsb3JlIgpGSUxURVIgPSAic2NoZW1hID09ICdvcGVuc3BlYy1kYXNoYm9hcmQvdjEnICYmIHN0YWdlID09ICdleHBsb3JlJyAmJiBhcHByb3ZhbCA9PSAnZXhwbG9yZSciCkZJRUxEUyA9IHsidHlwZSI6ICJldmVudCIsICJzb3VyY2UiOiBTT1VSQ0UsICJvbiI6ICJleHBsb3JlLnJlcXVlc3RlZCIsICJmaWx0ZXIiOiBGSUxURVJ9CgoKY2xhc3MgQnJpZGdlRXJyb3IoRXhjZXB0aW9uKToKICAgIHBhc3MKCgpkZWYgcmVxdWlyZSh2YWx1ZSwgbWVzc2FnZSk6CiAgICBpZiBub3QgdmFsdWU6CiAgICAgICAgcmFpc2UgQnJpZGdlRXJyb3IobWVzc2FnZSkKCgpkZWYgaWRlbnRpZmllcih2YWx1ZSk6CiAgICB0cnk6CiAgICAgICAgcmV0dXJuIGlzaW5zdGFuY2UodmFsdWUsIHN0cikgYW5kIHN0cih1dWlkLlVVSUQodmFsdWUpKSA9PSB2YWx1ZQogICAgZXhjZXB0IChWYWx1ZUVycm9yLCBBdHRyaWJ1dGVFcnJvcik6CiAgICAgICAgcmV0dXJuIEZhbHNlCgoKZGVmIGVuY29kZSh2YWx1ZSk6CiAgICByZXR1cm4ganNvbi5kdW1wcyh2YWx1ZSwgZW5zdXJlX2FzY2lpPUZhbHNlLCBhbGxvd19uYW49RmFsc2UsIHNlcGFyYXRvcnM9KCIsIiwgIjoiKSkuZW5jb2RlKCkKCgpjbGFzcyBOb1JlZGlyZWN0KHVybGxpYi5yZXF1ZXN0LkhUVFBSZWRpcmVjdEhhbmRsZXIpOgogICAgZGVmIHJlZGlyZWN0X3JlcXVlc3Qoc2VsZiwgcmVxLCBmcCwgY29kZSwgbXNnLCBoZWFkZXJzLCBuZXd1cmwpOgogICAgICAgIHJldHVybiBOb25lCgoKZGVmIHJlcXVlc3RfanNvbih1cmwsICosIG1ldGhvZD0iR0VUIiwgYm9keT1Ob25lLCBoZWFkZXJzPU5vbmUpOgogICAgcmF3ID0gYm9keSBpZiBpc2luc3RhbmNlKGJvZHksIGJ5dGVzKSBlbHNlIE5vbmUgaWYgYm9keSBpcyBOb25lIGVsc2UgZW5jb2RlKGJvZHkpCiAgICByZXF1ZXN0ID0gdXJsbGliLnJlcXVlc3QuUmVxdWVzdCh1cmwsIGRhdGE9cmF3LCBtZXRob2Q9bWV0aG9kLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBoZWFkZXJzPXsiQ29udGVudC1UeXBlIjogImFwcGxpY2F0aW9uL2pzb24iLCAqKihoZWFkZXJzIG9yIHt9KX0pCiAgICB0cnk6CiAgICAgICAgd2l0aCB1cmxsaWIucmVxdWVzdC5idWlsZF9vcGVuZXIoTm9SZWRpcmVjdCkub3BlbihyZXF1ZXN0LCB0aW1lb3V0PTUpIGFzIHJlc3BvbnNlOgogICAgICAgICAgICByZXN1bHQgPSByZXNwb25zZS5yZWFkKDFfMDAwXzAwMSkKICAgICAgICByZXF1aXJlKGxlbihyZXN1bHQpIDw9IDFfMDAwXzAwMCwgIkF1dG9tYXRpb24gcmVzcG9uc2UgZXhjZWVkZWQgaXRzIHNpemUgbGltaXQiKQogICAgICAgIHJldHVybiBqc29uLmxvYWRzKHJlc3VsdCkKICAgIGV4Y2VwdCB1cmxsaWIuZXJyb3IuSFRUUEVycm9yIGFzIGVycm9yOgogICAgICAgIHN0YXR1cyA9IGVycm9yLmNvZGUKICAgICAgICBlcnJvci5jbG9zZSgpCiAgICAgICAgcmFpc2UgQnJpZGdlRXJyb3IoZiJBdXRvbWF0aW9uIHJlcXVlc3QgZmFpbGVkIChIVFRQIHtzdGF0dXN9KSIpIGZyb20gTm9uZQogICAgZXhjZXB0ICh1cmxsaWIuZXJyb3IuVVJMRXJyb3IsIFRpbWVvdXRFcnJvciwgT1NFcnJvciwgVmFsdWVFcnJvcik6CiAgICAgICAgcmFpc2UgQnJpZGdlRXJyb3IoIkF1dG9tYXRpb24gcmVxdWVzdCBmYWlsZWQgb3IgcmV0dXJuZWQgaW52YWxpZCBkYXRhIikgZnJvbSBOb25lCgoKZGVmIGF0b21pY19qc29uKHBhdGgsIHZhbHVlKToKICAgIGRlc2NyaXB0b3IsIHRlbXBvcmFyeSA9IHRlbXBmaWxlLm1rc3RlbXAoZGlyPXBhdGgucGFyZW50KQogICAgdHJ5OgogICAgICAgIHdpdGggb3MuZmRvcGVuKGRlc2NyaXB0b3IsICJ3YiIpIGFzIHN0cmVhbToKICAgICAgICAgICAgc3RyZWFtLndyaXRlKGVuY29kZSh2YWx1ZSkpCiAgICAgICAgICAgIHN0cmVhbS5mbHVzaCgpCiAgICAgICAgICAgIG9zLmZzeW5jKHN0cmVhbS5maWxlbm8oKSkKICAgICAgICBvcy5yZXBsYWNlKHRlbXBvcmFyeSwgcGF0aCkKICAgIGZpbmFsbHk6CiAgICAgICAgaWYgb3MucGF0aC5leGlzdHModGVtcG9yYXJ5KToKICAgICAgICAgICAgb3MudW5saW5rKHRlbXBvcmFyeSkKCgpkZWYgcmVhZF9qc29uKHBhdGgpOgogICAgaWYgbm90IHBhdGguZXhpc3RzKCk6CiAgICAgICAgcmV0dXJuIE5vbmUKICAgIHJlcXVpcmUocGF0aC5pc19maWxlKCkgYW5kIG5vdCBwYXRoLmlzX3N5bWxpbmsoKSwgIkJyaWRnZSBzdGF0ZSBpcyBub3QgYSByZWd1bGFyIGZpbGUiKQogICAgcmVxdWlyZShwYXRoLnN0YXQoKS5zdF9zaXplIDwgNjU1MzYsICJCcmlkZ2Ugc3RhdGUgZXhjZWVkZWQgaXRzIHNpemUgbGltaXQiKQogICAgcmV0dXJuIGpzb24ubG9hZHMocGF0aC5yZWFkX3RleHQoKSkKCgpjbGFzcyBCcmlkZ2U6CiAgICBkZWYgX19pbml0X18oc2VsZiwgc2VydmljZSwgaG9tZSwgKiwgZW52PU5vbmUsIHJlcXVlc3Rlcj1yZXF1ZXN0X2pzb24pOgogICAgICAgIGVudiA9IG9zLmVudmlyb24gaWYgZW52IGlzIE5vbmUgZWxzZSBlbnYKICAgICAgICByZXF1aXJlKGlzaW5zdGFuY2Uoc2VydmljZSwgZGljdCksICJBdXRvbWF0aW9uIHJ1bnRpbWUgc2VydmljZSBpcyBub3QgYXZhaWxhYmxlIG9uIHRoaXMgYmFja2VuZCIpCiAgICAgICAgb3JpZ2luID0gc2VydmljZS5nZXQoInVybF9mcm9tX2FnZW50IiwgIiIpCiAgICAgICAgdHJ5OgogICAgICAgICAgICBwYXJzZWQgPSB1cmxsaWIucGFyc2UudXJsc3BsaXQob3JpZ2luKQogICAgICAgICAgICBwYXJzZWQucG9ydAogICAgICAgIGV4Y2VwdCAoVmFsdWVFcnJvciwgVHlwZUVycm9yKToKICAgICAgICAgICAgcmFpc2UgQnJpZGdlRXJyb3IoIkludmFsaWQgQXV0b21hdGlvbiBzZXJ2aWNlIGFkZHJlc3MiKSBmcm9tIE5vbmUKICAgICAgICByZXF1aXJlKHBhcnNlZC5zY2hlbWUgaW4gKCJodHRwIiwgImh0dHBzIikgYW5kIHBhcnNlZC5ob3N0bmFtZSBpbiAoImxvY2FsaG9zdCIsICIxMjcuMC4wLjEiLCAiOjoxIikKICAgICAgICAgICAgICAgIGFuZCBub3QgcGFyc2VkLnVzZXJuYW1lIGFuZCBub3QgcGFyc2VkLnBhc3N3b3JkIGFuZCBwYXJzZWQucGF0aCBpbiAoIiIsICIvIikKICAgICAgICAgICAgICAgIGFuZCBub3QgcGFyc2VkLnF1ZXJ5IGFuZCBub3QgcGFyc2VkLmZyYWdtZW50LCAiT25seSB0aGUgYWR2ZXJ0aXNlZCBsb2NhbCBBdXRvbWF0aW9uIHNlcnZpY2UgaXMgc3VwcG9ydGVkIikKICAgICAgICByZXF1aXJlKHNlcnZpY2UuZ2V0KCJhcGlfcHJlZml4IikgPT0gIi9hcGkvYXV0b21hdGlvbiIKICAgICAgICAgICAgICAgIGFuZCBzZXJ2aWNlLmdldCgiYXV0aF9lbnZfdmFyIikgPT0gIk9QRU5IQU5EU19BVVRPTUFUSU9OX0FQSV9LRVkiLAogICAgICAgICAgICAgICAgIlVuc3VwcG9ydGVkIEF1dG9tYXRpb24gYXV0aGVudGljYXRpb24gb3IgQVBJIHByZWZpeCIpCiAgICAgICAgc2VsZi5rZXkgPSBlbnYuZ2V0KCJPUEVOSEFORFNfQVVUT01BVElPTl9BUElfS0VZIikKICAgICAgICByZXF1aXJlKGlzaW5zdGFuY2Uoc2VsZi5rZXksIHN0cikgYW5kIHNlbGYua2V5LCAiQWdlbnQgU2VydmVyIGhhcyBubyBpbmplY3RlZCBBdXRvbWF0aW9uIGtleTsgdXNlIHRoZSBuYXRpdmUgbG9jYWwgQ2FudmFzIGxhdW5jaGVyIikKICAgICAgICByZXF1aXJlKGlzaW5zdGFuY2UoaG9tZSwgc3RyKSBhbmQgUGF0aChob21lKS5pc19hYnNvbHV0ZSgpIGFuZCBQYXRoKGhvbWUpLnJlc29sdmUoKSA9PSBQYXRoLmhvbWUoKS5yZXNvbHZlKCksCiAgICAgICAgICAgICAgICAiQWdlbnQgU2VydmVyIGhvbWUgZG9lcyBub3QgbWF0Y2ggdGhlIGhlbHBlcidzIGxvY2FsIGhvbWUiKQogICAgICAgIHNlbGYuYmFzZSA9IG9yaWdpbi5yc3RyaXAoIi8iKSArICIvYXBpL2F1dG9tYXRpb24vdjEiCiAgICAgICAgc2VsZi5yb290ID0gUGF0aChob21lKSAvICIub3BlbmhhbmRzL2FwcHMvb3BlbnNwZWMtcHJvZ3Jlc3MvYXV0b21hdGlvbiIgLyBoYXNobGliLnNoYTI1NihzZWxmLmJhc2UuZW5jb2RlKCkpLmhleGRpZ2VzdCgpWzoxNl0KICAgICAgICBzZWxmLnJlcXVlc3RlciA9IHJlcXVlc3RlcgoKICAgIGRlZiBhcGkoc2VsZiwgcGF0aCwgKiwgbWV0aG9kPSJHRVQiLCBib2R5PU5vbmUpOgogICAgICAgIHJldHVybiBzZWxmLnJlcXVlc3RlcihzZWxmLmJhc2UgKyBwYXRoLCBtZXRob2Q9bWV0aG9kLCBib2R5PWJvZHksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGhlYWRlcnM9eyJYLVNlc3Npb24tQVBJLUtleSI6IHNlbGYua2V5fSkKCiAgICBkZWYgYXV0b21hdGlvbihzZWxmLCBleHBlY3RlZF9pZD1Ob25lKToKICAgICAgICBpbnZlbnRvcnkgPSBzZWxmLmFwaSgiP2xpbWl0PTEwMCIpCiAgICAgICAgcmVxdWlyZShpc2luc3RhbmNlKGludmVudG9yeSwgZGljdCkgYW5kIGlzaW5zdGFuY2UoaW52ZW50b3J5LmdldCgiYXV0b21hdGlvbnMiKSwgbGlzdCkKICAgICAgICAgICAgICAgIGFuZCBpc2luc3RhbmNlKGludmVudG9yeS5nZXQoInRvdGFsIiksIGludCkgYW5kIGludmVudG9yeVsidG90YWwiXSA8PSAxMDAsCiAgICAgICAgICAgICAgICAiQ2Fubm90IGluc3BlY3QgdGhlIGNvbXBsZXRlIEF1dG9tYXRpb24gaW52ZW50b3J5IChtYXhpbXVtIDEwMCBkZWZpbml0aW9ucykiKQogICAgICAgIG1hdGNoZXMgPSBbaXRlbSBmb3IgaXRlbSBpbiBpbnZlbnRvcnlbImF1dG9tYXRpb25zIl0gaWYgaXNpbnN0YW5jZShpdGVtLCBkaWN0KSBhbmQgaXRlbS5nZXQoIm5hbWUiKSA9PSBOQU1FXQogICAgICAgIHJlcXVpcmUobGVuKG1hdGNoZXMpID09IDEgYW5kIGlkZW50aWZpZXIobWF0Y2hlc1swXS5nZXQoImlkIikpLCAiVGhlIGV4aXN0aW5nIEV4cGxvcmUgYXV0b21hdGlvbiBpcyBtaXNzaW5nIG9yIGFtYmlndW91cyIpCiAgICAgICAgaXRlbSA9IG1hdGNoZXNbMF0KICAgICAgICByZXF1aXJlKGV4cGVjdGVkX2lkIGlzIE5vbmUgb3IgaXRlbVsiaWQiXSA9PSBleHBlY3RlZF9pZCwgIlRoZSBzZWxlY3RlZCBFeHBsb3JlIGF1dG9tYXRpb24gY2hhbmdlZDsgcmVjb25uZWN0IGJlZm9yZSBydW5uaW5nIikKICAgICAgICByZXR1cm4gaXRlbQoKICAgIGRlZiByZWFkeV9hdXRvbWF0aW9uKHNlbGYsIGl0ZW0pOgogICAgICAgIHRyaWdnZXIgPSBpdGVtLmdldCgidHJpZ2dlciIsIHt9KQogICAgICAgIHJlcXVpcmUoaXNpbnN0YW5jZSh0cmlnZ2VyLCBkaWN0KSBhbmQgYWxsKHRyaWdnZXIuZ2V0KGtleSkgPT0gdmFsdWUgZm9yIGtleSwgdmFsdWUgaW4gRklFTERTLml0ZW1zKCkpCiAgICAgICAgICAgICAgICBhbmQgdHJpZ2dlci5nZXQoImRlc3RpbmF0aW9uIiwgImRpc3BhdGNoX3J1biIpID09ICJkaXNwYXRjaF9ydW4iCiAgICAgICAgICAgICAgICBhbmQgaXRlbS5nZXQoInN0YXRlIikgPT0gIkFDVElWRSIgYW5kIGl0ZW0uZ2V0KCJlbmFibGVkIikgaXMgVHJ1ZSwKICAgICAgICAgICAgICAgICJTeW5jIHRoZSB1cGRhdGVkIEV4cGxvcmUgZGVmaW5pdGlvbiBiZWZvcmUgdXNpbmcgZGFzaGJvYXJkIGlucHV0cyIpCgogICAgZGVmIGNvbmZpZyhzZWxmKToKICAgICAgICByZXR1cm4gcmVhZF9qc29uKHNlbGYucm9vdCAvICJjb25uZWN0aW9uLmpzb24iKQoKICAgIGRlZiBwcm9iZShzZWxmKToKICAgICAgICBpdGVtID0gc2VsZi5hdXRvbWF0aW9uKCkKICAgICAgICB0cnk6CiAgICAgICAgICAgIHNlbGYucmVhZHlfYXV0b21hdGlvbihpdGVtKQogICAgICAgICAgICBjb25maWcgPSBzZWxmLmNvbmZpZygpCiAgICAgICAgICAgIHJlYWR5ID0gYm9vbChjb25maWcgYW5kIGNvbmZpZy5nZXQoInN0YXRlIikgPT0gInJlYWR5IikKICAgICAgICAgICAgbWVzc2FnZSA9ICJDb25uZWN0ZWQgdG8gdGhlIGV4aXN0aW5nIEV4cGxvcmUgYXV0b21hdGlvbi4iIGlmIHJlYWR5IGVsc2UgIkNvbm5lY3QgRXhwbG9yZSBvbmNlIHRvIGVuYWJsZSBzaWduZWQgbG9jYWwgcmVxdWVzdHMuIgogICAgICAgIGV4Y2VwdCBCcmlkZ2VFcnJvciBhcyBlcnJvcjoKICAgICAgICAgICAgcmVhZHksIG1lc3NhZ2UgPSBGYWxzZSwgc3RyKGVycm9yKQogICAgICAgIHJldHVybiB7ImtpbmQiOiAicHJvYmUiLCAicmVhZHkiOiByZWFkeSwgIm1lc3NhZ2UiOiBtZXNzYWdlLAogICAgICAgICAgICAgICAgImF1dG9tYXRpb24iOiB7ImlkIjogaXRlbVsiaWQiXSwgIm5hbWUiOiBOQU1FfX0KCiAgICBAY29udGV4dGxpYi5jb250ZXh0bWFuYWdlcgogICAgZGVmIGxvY2soc2VsZik6CiAgICAgICAgc2VsZi5yb290Lm1rZGlyKHBhcmVudHM9VHJ1ZSwgZXhpc3Rfb2s9VHJ1ZSwgbW9kZT0wbzcwMCkKICAgICAgICByZXF1aXJlKG5vdCBzZWxmLnJvb3QuaXNfc3ltbGluaygpLCAiQnJpZGdlIHN0YXRlIGRpcmVjdG9yeSBtdXN0IG5vdCBiZSBhIHN5bWxpbmsiKQogICAgICAgIHdpdGggKHNlbGYucm9vdCAvICIubG9jayIpLm9wZW4oImEiKSBhcyBsb2NrOgogICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICBmY250bC5mbG9jayhsb2NrLCBmY250bC5MT0NLX0VYIHwgZmNudGwuTE9DS19OQikKICAgICAgICAgICAgZXhjZXB0IEJsb2NraW5nSU9FcnJvcjoKICAgICAgICAgICAgICAgIHJhaXNlIEJyaWRnZUVycm9yKCJBbm90aGVyIEV4cGxvcmUgcmVxdWVzdCBpcyBiZWluZyBwcm9jZXNzZWQ7IGNoZWNrIGl0cyByZXN1bHQgZmlyc3QiKSBmcm9tIE5vbmUKICAgICAgICAgICAgeWllbGQKCiAgICBkZWYgc2V0dXAoc2VsZik6CiAgICAgICAgaXRlbSA9IHNlbGYuYXV0b21hdGlvbigpCiAgICAgICAgc2VsZi5yZWFkeV9hdXRvbWF0aW9uKGl0ZW0pCiAgICAgICAgd2l0aCBzZWxmLmxvY2soKToKICAgICAgICAgICAgY29uZmlnID0gc2VsZi5jb25maWcoKQogICAgICAgICAgICBpZiBjb25maWcgYW5kIGNvbmZpZy5nZXQoInN0YXRlIikgPT0gInJlYWR5IjoKICAgICAgICAgICAgICAgIHJldHVybiB7ImtpbmQiOiAic2V0dXAiLCAicmVhZHkiOiBUcnVlLCAiYXV0b21hdGlvbiI6IHsiaWQiOiBpdGVtWyJpZCJdLCAibmFtZSI6IE5BTUV9fQogICAgICAgICAgICByZXF1aXJlKGNvbmZpZyBpcyBOb25lLCAiQW4gZWFybGllciBjb25uZWN0aW9uIGF0dGVtcHQgaGFzIGFuIHVua25vd24gb3V0Y29tZTsgaW5zcGVjdCB0aGUgbG9jYWwgY29ubmVjdGlvbiBzdGF0ZSBiZWZvcmUgcmV0cnlpbmciKQogICAgICAgICAgICBleGlzdGluZyA9IHNlbGYuYXBpKCIvd2ViaG9va3M/bGltaXQ9MTAwIikKICAgICAgICAgICAgcmVxdWlyZShpc2luc3RhbmNlKGV4aXN0aW5nLCBkaWN0KSBhbmQgaXNpbnN0YW5jZShleGlzdGluZy5nZXQoIndlYmhvb2tzIiksIGxpc3QpCiAgICAgICAgICAgICAgICAgICAgYW5kIGV4aXN0aW5nLmdldCgidG90YWwiLCAxMDEpIDw9IDEwMCwgIkNhbm5vdCBpbnNwZWN0IHRoZSBjb21wbGV0ZSBsb2NhbCBzb3VyY2UgaW52ZW50b3J5IikKICAgICAgICAgICAgcmVxdWlyZShub3QgYW55KHJvdy5nZXQoInNvdXJjZSIpID09IFNPVVJDRSBmb3Igcm93IGluIGV4aXN0aW5nWyJ3ZWJob29rcyJdKSwKICAgICAgICAgICAgICAgICAgICAiVGhlIGRhc2hib2FyZCBzb3VyY2UgYWxyZWFkeSBleGlzdHMgd2l0aG91dCBhIHNhdmVkIGxvY2FsIGNvbm5lY3Rpb247IGRvIG5vdCBvdmVyd3JpdGUgaXRzIHNlY3JldCIpCiAgICAgICAgICAgIGNvbmZpZyA9IHsic3RhdGUiOiAicmVnaXN0ZXJpbmciLCAic2VjcmV0Ijogc2VjcmV0cy50b2tlbl91cmxzYWZlKDMyKX0KICAgICAgICAgICAgYXRvbWljX2pzb24oc2VsZi5yb290IC8gImNvbm5lY3Rpb24uanNvbiIsIGNvbmZpZykKICAgICAgICAgICAgY3JlYXRlZCA9IHNlbGYuYXBpKCIvd2ViaG9va3MiLCBtZXRob2Q9IlBPU1QiLCBib2R5PXsKICAgICAgICAgICAgICAgICJuYW1lIjogIk9wZW5TcGVjIGRhc2hib2FyZCDCtyBleHBsaWNpdCBFeHBsb3JlIHJlcXVlc3RzIiwgInNvdXJjZSI6IFNPVVJDRSwKICAgICAgICAgICAgICAgICJldmVudF9rZXlfZXhwciI6ICJ0eXBlIiwgInNpZ25hdHVyZV9oZWFkZXIiOiAiWC1TaWduYXR1cmUtMjU2IiwKICAgICAgICAgICAgICAgICJzaWduYXR1cmVfc2NoZW1lIjogImhtYWNfc2hhMjU2X2hleCIsICJ3ZWJob29rX3NlY3JldCI6IGNvbmZpZ1sic2VjcmV0Il0sCiAgICAgICAgICAgIH0pCiAgICAgICAgICAgIHJlcXVpcmUoaXNpbnN0YW5jZShjcmVhdGVkLCBkaWN0KSBhbmQgaWRlbnRpZmllcihjcmVhdGVkLmdldCgib3JnX2lkIikpIGFuZCBjcmVhdGVkLmdldCgic291cmNlIikgPT0gU09VUkNFLAogICAgICAgICAgICAgICAgICAgICJTb3VyY2UgY3JlYXRpb24gcmV0dXJuZWQgdW5leHBlY3RlZCBkYXRhOyBpbnNwZWN0IHRoZSBsb2NhbCBjb25uZWN0aW9uIHN0YXRlIikKICAgICAgICAgICAgY29uZmlnLnVwZGF0ZShzdGF0ZT0icmVhZHkiLCBvcmdfaWQ9Y3JlYXRlZFsib3JnX2lkIl0pCiAgICAgICAgICAgIGF0b21pY19qc29uKHNlbGYucm9vdCAvICJjb25uZWN0aW9uLmpzb24iLCBjb25maWcpCiAgICAgICAgcmV0dXJuIHsia2luZCI6ICJzZXR1cCIsICJyZWFkeSI6IFRydWUsICJhdXRvbWF0aW9uIjogeyJpZCI6IGl0ZW1bImlkIl0sICJuYW1lIjogTkFNRX19CgogICAgZGVmIGRpc3BhdGNoKHNlbGYsIGRhdGEpOgogICAgICAgIGZpZWxkcyA9IHsiYXV0b21hdGlvbl9pZCIsICJyZXF1ZXN0X2lkIiwgIndvcmtzcGFjZSIsICJjaGFuZ2UiLCAicmVxdWVzdCIsICJwYXJhbWV0ZXJzIn0KICAgICAgICByZXF1aXJlKGlzaW5zdGFuY2UoZGF0YSwgZGljdCkgYW5kIHNldChkYXRhKSA9PSBmaWVsZHMsICJVbmV4cGVjdGVkIEV4cGxvcmUgaW5wdXQgZmllbGRzIikKICAgICAgICByZXF1aXJlKGlkZW50aWZpZXIoZGF0YVsiYXV0b21hdGlvbl9pZCJdKSBhbmQgaWRlbnRpZmllcihkYXRhWyJyZXF1ZXN0X2lkIl0pLCAiSW52YWxpZCBhdXRvbWF0aW9uIG9yIHJlcXVlc3QgSUQiKQogICAgICAgIHJlcXVpcmUoaXNpbnN0YW5jZShkYXRhWyJ3b3Jrc3BhY2UiXSwgc3RyKSBhbmQgUGF0aChkYXRhWyJ3b3Jrc3BhY2UiXSkuaXNfYWJzb2x1dGUoKQogICAgICAgICAgICAgICAgYW5kICJceDAwIiBub3QgaW4gZGF0YVsid29ya3NwYWNlIl0gYW5kICJcbiIgbm90IGluIGRhdGFbIndvcmtzcGFjZSJdLCAiV29ya3NwYWNlIG11c3QgYmUgYW4gYWJzb2x1dGUgbG9jYWwgZGlyZWN0b3J5IikKICAgICAgICByZXF1aXJlKGlzaW5zdGFuY2UoZGF0YVsiY2hhbmdlIl0sIHN0cikgYW5kIGxlbihkYXRhWyJjaGFuZ2UiXSkgPD0gMTAwCiAgICAgICAgICAgICAgICBhbmQgcmUuZnVsbG1hdGNoKHIiW2EtejAtOV0rKD86LVthLXowLTldKykqIiwgZGF0YVsiY2hhbmdlIl0pLCAiQ2hhbmdlIG11c3QgYmUgYSBrZWJhYi1jYXNlIG5hbWUiKQogICAgICAgIHJlcXVpcmUoaXNpbnN0YW5jZShkYXRhWyJyZXF1ZXN0Il0sIHN0cikgYW5kIGRhdGFbInJlcXVlc3QiXS5zdHJpcCgpIGFuZCBsZW4oZGF0YVsicmVxdWVzdCJdKSA8PSAxMDAwMCwKICAgICAgICAgICAgICAgICJFbnRlciBhbiBFeHBsb3JlIHByb21wdCBvZiBhdCBtb3N0IDEwMDAwIGNoYXJhY3RlcnMiKQogICAgICAgIHJlcXVpcmUoaXNpbnN0YW5jZShkYXRhWyJwYXJhbWV0ZXJzIl0sIGRpY3QpIGFuZCBsZW4oZW5jb2RlKGRhdGFbInBhcmFtZXRlcnMiXSkpIDw9IDgxOTIsCiAgICAgICAgICAgICAgICAiUGFyYW1ldGVycyBtdXN0IGJlIGEgSlNPTiBvYmplY3Qgb2YgYXQgbW9zdCA4IEtpQiIpCiAgICAgICAgaXRlbSA9IHNlbGYuYXV0b21hdGlvbihkYXRhWyJhdXRvbWF0aW9uX2lkIl0pCiAgICAgICAgc2VsZi5yZWFkeV9hdXRvbWF0aW9uKGl0ZW0pCiAgICAgICAgIyBSZWZ1c2UgYW1iaWd1b3VzIHJvdXRpbmcgYmVmb3JlIHNlbmRpbmcgYW4gZXZlbnQuIE5vIHNoYXJlZCBkZWZpbml0aW9uCiAgICAgICAgIyBpcyBjaGFuZ2VkIGZvciBhIHJ1bjsgZWFjaCBldmVudCBjYXJyaWVzIGl0cyBvd24gaW1tdXRhYmxlIGlucHV0LgogICAgICAgIGludmVudG9yeSA9IHNlbGYuYXBpKCI/bGltaXQ9MTAwIikKICAgICAgICByZXF1aXJlKG5vdCBhbnkocm93LmdldCgiaWQiKSAhPSBpdGVtWyJpZCJdIGFuZCByb3cuZ2V0KCJlbmFibGVkIikKICAgICAgICAgICAgICAgICAgICAgICAgYW5kIHJvdy5nZXQoInRyaWdnZXIiLCB7fSkuZ2V0KCJzb3VyY2UiKSA9PSBTT1VSQ0UgZm9yIHJvdyBpbiBpbnZlbnRvcnlbImF1dG9tYXRpb25zIl0pLAogICAgICAgICAgICAgICAgIk1vcmUgdGhhbiBvbmUgYXV0b21hdGlvbiB1c2VzIHRoZSBkYXNoYm9hcmQgc291cmNlOyByZXNvbHZlIHJvdXRpbmcgYmVmb3JlIHJ1bm5pbmciKQogICAgICAgIGZpbmdlcnByaW50ID0gaGFzaGxpYi5zaGEyNTYoZW5jb2RlKGRhdGEpKS5oZXhkaWdlc3QoKQogICAgICAgIHdpdGggc2VsZi5sb2NrKCk6CiAgICAgICAgICAgIGNvbmZpZyA9IHNlbGYuY29uZmlnKCkKICAgICAgICAgICAgcmVxdWlyZShjb25maWcgYW5kIGNvbmZpZy5nZXQoInN0YXRlIikgPT0gInJlYWR5IiBhbmQgaWRlbnRpZmllcihjb25maWcuZ2V0KCJvcmdfaWQiKSksICJDb25uZWN0IEV4cGxvcmUgYmVmb3JlIHJ1bm5pbmcgaXQiKQogICAgICAgICAgICBqb3VybmFsID0gc2VsZi5yb290IC8gKGRhdGFbInJlcXVlc3RfaWQiXSArICIuanNvbiIpCiAgICAgICAgICAgIHJlY29yZCA9IHJlYWRfanNvbihqb3VybmFsKQogICAgICAgICAgICBpZiByZWNvcmQ6CiAgICAgICAgICAgICAgICByZXF1aXJlKHJlY29yZC5nZXQoImZpbmdlcnByaW50IikgPT0gZmluZ2VycHJpbnQsICJUaGlzIHJlcXVlc3QgSUQgYmVsb25ncyB0byBkaWZmZXJlbnQgaW5wdXRzIikKICAgICAgICAgICAgICAgIHJlcXVpcmUocmVjb3JkLmdldCgic3RhdGUiKSA9PSAiZGlzcGF0Y2hlZCIsICJUaGlzIHJlcXVlc3QgbWF5IGFscmVhZHkgaGF2ZSBzdGFydGVkOyBpbnNwZWN0IEF1dG9tYXRpb24gaGlzdG9yeSBiZWZvcmUgY3JlYXRpbmcgYW5vdGhlciIpCiAgICAgICAgICAgICAgICByZXR1cm4geyJraW5kIjogImRpc3BhdGNoIiwgKip7a2V5OiByZWNvcmRba2V5XSBmb3Iga2V5IGluICgiYXV0b21hdGlvbl9pZCIsICJyZXF1ZXN0X2lkIiwgInJ1bl9pZCIpfX0KICAgICAgICAgICAgZXZlbnQgPSB7InNjaGVtYSI6ICJvcGVuc3BlYy1kYXNoYm9hcmQvdjEiLCAidHlwZSI6ICJleHBsb3JlLnJlcXVlc3RlZCIsICJzdGFnZSI6ICJleHBsb3JlIiwgImFwcHJvdmFsIjogImV4cGxvcmUiLAogICAgICAgICAgICAgICAgICAgICAqKntrZXk6IGRhdGFba2V5XSBmb3Iga2V5IGluICgicmVxdWVzdF9pZCIsICJ3b3Jrc3BhY2UiLCAiY2hhbmdlIiwgInJlcXVlc3QiLCAicGFyYW1ldGVycyIpfX0KICAgICAgICAgICAgcmVjb3JkID0geyJzdGF0ZSI6ICJkaXNwYXRjaGluZyIsICJmaW5nZXJwcmludCI6IGZpbmdlcnByaW50LCAiYXV0b21hdGlvbl9pZCI6IGl0ZW1bImlkIl0sICJyZXF1ZXN0X2lkIjogZGF0YVsicmVxdWVzdF9pZCJdfQogICAgICAgICAgICBhdG9taWNfanNvbihqb3VybmFsLCByZWNvcmQpCiAgICAgICAgICAgIHJhdyA9IGVuY29kZShldmVudCkKICAgICAgICAgICAgc2lnbmF0dXJlID0gInNoYTI1Nj0iICsgaG1hYy5uZXcoY29uZmlnWyJzZWNyZXQiXS5lbmNvZGUoKSwgcmF3LCBoYXNobGliLnNoYTI1NikuaGV4ZGlnZXN0KCkKICAgICAgICAgICAgcmVzdWx0ID0gc2VsZi5yZXF1ZXN0ZXIoc2VsZi5iYXNlICsgZiIvZXZlbnRzL3tjb25maWdbJ29yZ19pZCddfS97U09VUkNFfSIsIG1ldGhvZD0iUE9TVCIsIGJvZHk9cmF3LAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBoZWFkZXJzPXsiWC1TaWduYXR1cmUtMjU2Ijogc2lnbmF0dXJlfSkKICAgICAgICAgICAgcmVxdWlyZShpc2luc3RhbmNlKHJlc3VsdCwgZGljdCkgYW5kIHJlc3VsdC5nZXQoInJlY2VpdmVkIikgaXMgVHJ1ZSBhbmQgcmVzdWx0LmdldCgibWF0Y2hlZCIpID09IDEKICAgICAgICAgICAgICAgICAgICBhbmQgbGVuKHJlc3VsdC5nZXQoInJ1bnNfY3JlYXRlZCIsIFtdKSkgPT0gMSBhbmQgaWRlbnRpZmllcihyZXN1bHRbInJ1bnNfY3JlYXRlZCJdWzBdKSwKICAgICAgICAgICAgICAgICAgICAiRXhwZWN0ZWQgZXhhY3RseSBvbmUgRXhwbG9yZSBydW47IGluc3BlY3QgQXV0b21hdGlvbiBoaXN0b3J5IGJlZm9yZSB0cnlpbmcgYWdhaW4iKQogICAgICAgICAgICByZWNvcmQudXBkYXRlKHN0YXRlPSJkaXNwYXRjaGVkIiwgcnVuX2lkPXJlc3VsdFsicnVuc19jcmVhdGVkIl1bMF0pCiAgICAgICAgICAgIGF0b21pY19qc29uKGpvdXJuYWwsIHJlY29yZCkKICAgICAgICAgICAgcmV0dXJuIHsia2luZCI6ICJkaXNwYXRjaCIsICoqe2tleTogcmVjb3JkW2tleV0gZm9yIGtleSBpbiAoImF1dG9tYXRpb25faWQiLCAicmVxdWVzdF9pZCIsICJydW5faWQiKX19CgoKZGVmIGhhbmRsZSh2YWx1ZSk6CiAgICByZXF1aXJlKGlzaW5zdGFuY2UodmFsdWUsIGRpY3QpIGFuZCBzZXQodmFsdWUpIDw9IHsiYWN0aW9uIiwgInNlcnZpY2UiLCAiaG9tZSIsICJpbnB1dCJ9LCAiSW52YWxpZCBicmlkZ2UgcmVxdWVzdCIpCiAgICByZXF1aXJlKHZhbHVlLmdldCgiYWN0aW9uIikgaW4gKCJwcm9iZSIsICJzZXR1cCIsICJkaXNwYXRjaCIpLCAiVW5zdXBwb3J0ZWQgYnJpZGdlIGFjdGlvbiIpCiAgICBicmlkZ2UgPSBCcmlkZ2UodmFsdWUuZ2V0KCJzZXJ2aWNlIiksIHZhbHVlLmdldCgiaG9tZSIpKQogICAgaWYgdmFsdWVbImFjdGlvbiJdID09ICJkaXNwYXRjaCI6CiAgICAgICAgcmV0dXJuIGJyaWRnZS5kaXNwYXRjaCh2YWx1ZS5nZXQoImlucHV0IikpCiAgICByZXF1aXJlKCJpbnB1dCIgbm90IGluIHZhbHVlLCAiVW5leHBlY3RlZCBicmlkZ2UgaW5wdXRzIikKICAgIHJldHVybiBicmlkZ2UucHJvYmUoKSBpZiB2YWx1ZVsiYWN0aW9uIl0gPT0gInByb2JlIiBlbHNlIGJyaWRnZS5zZXR1cCgpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHRyeToKICAgICAgICByZXF1aXJlKGxlbihzeXMuYXJndikgPT0gMiBhbmQgbGVuKHN5cy5hcmd2WzFdKSA8PSA2NTUzNiwgIkludmFsaWQgYnJpZGdlIGlucHV0IikKICAgICAgICByZXN1bHQgPSBoYW5kbGUoanNvbi5sb2FkcyhiYXNlNjQuYjY0ZGVjb2RlKHN5cy5hcmd2WzFdLCB2YWxpZGF0ZT1UcnVlKSkpCiAgICAgICAgcHJpbnQoanNvbi5kdW1wcyh7InZlcnNpb24iOiAxLCAqKnJlc3VsdH0sIGVuc3VyZV9hc2NpaT1GYWxzZSkpCiAgICBleGNlcHQgQnJpZGdlRXJyb3IgYXMgZXJyb3I6CiAgICAgICAgcHJpbnQoanNvbi5kdW1wcyh7InZlcnNpb24iOiAxLCAia2luZCI6ICJlcnJvciIsICJtZXNzYWdlIjogc3RyKGVycm9yKX0pKQogICAgICAgIHN5cy5leGl0KDEpCiAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgIHByaW50KGpzb24uZHVtcHMoeyJ2ZXJzaW9uIjogMSwgImtpbmQiOiAiZXJyb3IiLCAibWVzc2FnZSI6ICJDb3VsZCBub3QgY29tcGxldGUgdGhlIGxvY2FsIEF1dG9tYXRpb24gcmVxdWVzdDsgaW5zcGVjdCBpdHMgaGlzdG9yeSBiZWZvcmUgcmV0cnlpbmcifSkpCiAgICAgICAgc3lzLmV4aXQoMSkK"), (character) => character.charCodeAt(0)));

// src/automation.js
var UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
var quote = (value) => "'" + value.replaceAll("'", "'\\''") + "'";
function validateExploreInput({ workspace, change, request, parameters }) {
  if (typeof workspace !== "string" || !workspace.startsWith("/") || /[\0\r\n]/.test(workspace)) {
    throw new Error("Load a valid local OpenSpec project first.");
  }
  if (typeof change !== "string" || change.length > 100 || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(change)) {
    throw new Error("Enter a kebab-case change name, such as add-task-labels.");
  }
  if (typeof request !== "string" || !request.trim() || request.length > 1e4) {
    throw new Error("Enter an Explore prompt of at most 10000 characters.");
  }
  if (!parameters || typeof parameters !== "object" || Array.isArray(parameters) || new TextEncoder().encode(JSON.stringify(parameters)).length > 8192) {
    throw new Error("Parameters must be a JSON object of at most 8 KiB.");
  }
  return { workspace, change, request, parameters };
}
async function callAutomation(host, action, input) {
  const [info, home] = await Promise.all([
    host.agentServer.request({ method: "GET", path: "/server_info" }),
    host.agentServer.request({ method: "GET", path: "/api/file/home" })
  ]);
  const service = info?.runtime_services?.services?.automation;
  if (!service || typeof home?.home !== "string") {
    throw new Error("This backend does not advertise a supported local Automation service. Open the app through the native Canvas stack.");
  }
  const payload = { action, service, home: home.home, ...input ? { input } : {} };
  const encoded = btoa(Array.from(new TextEncoder().encode(JSON.stringify(payload)), (byte) => String.fromCharCode(byte)).join(""));
  const output = await host.agentServer.request({
    method: "POST",
    path: "/api/bash/execute_bash_command",
    body: { command: `python3 -c ${quote(automation_bridge_default)} ${quote(encoded)}`, cwd: home.home, timeout: 30 }
  });
  if (!output || output.order !== 0 || !Number.isInteger(output.exit_code) || typeof output.stdout !== "string" || output.stdout.length > 128 * 1024) {
    throw new Error("The Automation request did not return complete output. Inspect Automation history before starting another request.");
  }
  let data;
  try {
    data = JSON.parse(output.stdout);
  } catch {
    throw new Error("Invalid Automation response. Inspect Automation history before starting another request.");
  }
  if (data?.version === 1 && data.kind === "error" && typeof data.message === "string") throw new Error(data.message.slice(0, 600));
  if (output.exit_code !== 0 || data?.version !== 1 || data.kind !== action) throw new Error("Unexpected Automation response. Inspect its history before retrying.");
  if (action === "dispatch") {
    if (!UUID.test(data.run_id) || data.automation_id !== input.automation_id || data.request_id !== input.request_id) {
      throw new Error("The returned run does not match this request. Inspect Automation history.");
    }
  } else if (typeof data.ready !== "boolean" || !UUID.test(data.automation?.id) || typeof data.automation?.name !== "string") {
    throw new Error("Invalid Automation connection details.");
  }
  return data;
}
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== void 0) node.textContent = text;
  return node;
}
function mountAutomation({ host, container, navigate, getWorkspace, getChange }) {
  let disposed = false;
  let connected = null;
  let busy = false;
  let opened = false;
  let last = null;
  const key = `openhands.apps.openspec-progress:${host.backend.id}:last-explore`;
  try {
    const stored = JSON.parse(localStorage.getItem(key));
    if (stored && UUID.test(stored.request_id) && UUID.test(stored.automation_id) && (!stored.run_id || UUID.test(stored.run_id))) last = stored;
  } catch {
  }
  const remember = (value) => {
    last = value;
    try {
      if (value) localStorage.setItem(key, JSON.stringify(value));
      else localStorage.removeItem(key);
    } catch {
    }
  };
  const panel = el("details", "osp-automation");
  panel.append(el("summary", "", "Run Explore automation"));
  const body = el("div", "osp-automation-body");
  body.append(el("p", "osp-muted", "Send a requirement to the existing OpenSpec Explore automation. It investigates and stops for your review."));
  const connection = el("div", "osp-automation-connection");
  const connectionText = el("p", "osp-muted", "Open this panel to check the connection.");
  const connect = el("button", "osp-button", "Connect Explore");
  connect.type = "button";
  connect.disabled = true;
  connection.append(connectionText, connect);
  const disclosure = el("p", "osp-disclosure", "Connecting registers a signed local request source and saves its key privately on Agent Server. It adds no schedule and starts no agent.");
  const form = el("form", "osp-explore-form");
  const changeLabel = el("label", "osp-field");
  changeLabel.append(el("span", "osp-label", "Change name"));
  const change = el("input");
  change.setAttribute("aria-label", "Change name");
  change.placeholder = "add-task-labels";
  change.maxLength = 100;
  changeLabel.append(change);
  const promptLabel = el("label", "osp-field");
  promptLabel.append(el("span", "osp-label", "Requirement / prompt"));
  const prompt = el("textarea");
  prompt.setAttribute("aria-label", "Requirement / prompt");
  prompt.placeholder = "Describe the requirement, questions, and constraints to explore\u2026";
  prompt.maxLength = 1e4;
  prompt.rows = 4;
  promptLabel.append(prompt);
  const paramLabel = el("label", "osp-field");
  paramLabel.append(el("span", "osp-label", "Parameters (optional JSON object)"));
  const params = el("textarea");
  params.setAttribute("aria-label", "Parameters (optional JSON object)");
  params.value = "{}";
  params.rows = 2;
  params.spellcheck = false;
  paramLabel.append(params);
  const controls = el("div", "osp-actions");
  const submit = el("button", "osp-button osp-primary", "Run Explore");
  submit.type = "submit";
  const another = el("button", "osp-button", "Start another request");
  another.type = "button";
  another.hidden = true;
  controls.append(submit, another);
  form.append(changeLabel, promptLabel, paramLabel, el("p", "osp-disclosure", "This runs only Explore in this automation\u2019s configured workspace and profile. Parameters are investigation context; they do not override execution settings."), controls);
  const result = el("div", "osp-automation-result");
  result.setAttribute("role", "status");
  result.setAttribute("aria-live", "polite");
  body.append(connection, disclosure, form, result);
  panel.append(body);
  container.append(panel);
  function updateControls() {
    submit.disabled = busy || !connected?.ready || Boolean(last);
    connect.disabled = busy || Boolean(connected?.ready);
    prompt.disabled = change.disabled = params.disabled = busy || Boolean(last);
    another.hidden = !last;
    another.disabled = busy;
    submit.textContent = busy ? "Working\u2026" : "Run Explore";
  }
  function renderLast() {
    result.replaceChildren();
    if (!last) return;
    const link = el("a", "osp-run-link", last.run_id ? "Open automation run \u2192" : "Inspect automation history \u2192");
    link.href = `/automations/${last.automation_id}${last.run_id ? `?run=${last.run_id}` : ""}`;
    link.addEventListener("click", (event) => {
      event.preventDefault();
      navigate(link.getAttribute("href"));
    });
    result.append(
      el("p", "", last.run_id ? "Explore was submitted. Open the run for status, logs, and its conversation." : "This request may already have started. Inspect its history before starting another."),
      el("code", "osp-task-source", `Request ${last.request_id}`),
      link
    );
  }
  async function connectAction(action) {
    if (busy || disposed) return;
    busy = true;
    updateControls();
    connectionText.textContent = action === "setup" ? "Connecting the existing Explore automation\u2026" : "Checking the existing Explore automation\u2026";
    try {
      const value = await callAutomation(host, action);
      if (disposed) return;
      connected = value;
      connectionText.textContent = value.ready ? `Connected \xB7 ${value.automation.name}` : value.message;
      if (value.ready) disclosure.hidden = true;
    } catch (error) {
      if (!disposed) connectionText.textContent = error.message || "Cannot connect to the Automation service.";
    } finally {
      busy = false;
      if (!disposed) updateControls();
    }
  }
  panel.addEventListener("toggle", () => {
    if (!panel.open || opened) return;
    opened = true;
    change.value = getChange() || "";
    renderLast();
    connectAction("probe");
  });
  connect.addEventListener("click", () => connectAction("setup"));
  another.addEventListener("click", () => {
    remember(null);
    renderLast();
    updateControls();
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (busy || last || !connected?.ready || disposed) return;
    let input;
    try {
      let parameters;
      try {
        parameters = JSON.parse(params.value);
      } catch {
        throw new Error('Parameters must be valid JSON, for example {"focus":"accessibility"}.');
      }
      input = validateExploreInput({ workspace: getWorkspace(), change: change.value.trim(), request: prompt.value, parameters });
    } catch (error) {
      result.textContent = error.message;
      return;
    }
    busy = true;
    const attempt = { request_id: crypto.randomUUID(), automation_id: connected.automation.id };
    remember(attempt);
    updateControls();
    result.textContent = "Submitting one Explore request\u2026";
    try {
      const response = await callAutomation(host, "dispatch", { ...input, ...attempt });
      remember({ ...attempt, run_id: response.run_id });
      if (!disposed) renderLast();
    } catch (error) {
      if (!disposed) {
        renderLast();
        result.prepend(el("p", "osp-error", error.message || "The request outcome is unknown. Inspect Automation history."));
      }
    } finally {
      busy = false;
      if (!disposed) updateControls();
    }
  });
  updateControls();
  return () => {
    disposed = true;
    panel.remove();
  };
}

// src/extension.js
var DEFAULT_WORKSPACE = "/Users/oka/Desktop/openHanda-demo";
var STATE_LABELS = { done: "Done", ready: "Ready to write", blocked: "Blocked", skipped: "Skipped" };
function el2(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== void 0) node.textContent = text;
  return node;
}
function button(text, className, handler) {
  const node = el2("button", className, text);
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
  const bar = el2("div", "osp-progress");
  bar.setAttribute("role", "progressbar");
  bar.setAttribute("aria-label", label);
  bar.setAttribute("aria-valuemin", "0");
  bar.setAttribute("aria-valuemax", String(total || 1));
  bar.setAttribute("aria-valuenow", String(done));
  const fill = el2("span");
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
    let disposeAutomation;
    const requested = path ? /^changes\/([a-z0-9]+(?:-[a-z0-9]+)*)$/.exec(path) : null;
    const root = el2("section", "osp-root");
    const style = el2("style");
    style.dataset.openspecProgress = "true";
    style.textContent = styles_default;
    root.append(style);
    container.append(root);
    function dispose() {
      disposed = true;
      generation++;
      disposeAutomation?.();
      root.remove();
      disposers.delete(dispose);
    }
    disposers.add(dispose);
    if (path && !requested) {
      root.append(
        el2("h1", "", "Page not found"),
        el2("p", "osp-muted", "This OpenSpec progress route is not available."),
        button("Back to progress", "osp-button", () => navigate(base))
      );
      return dispose;
    }
    if (host.backend.kind !== "local") {
      root.append(
        el2("h1", "", "OpenSpec progress"),
        el2("p", "osp-error", "Connect a supported Agent Server with a local OpenSpec workspace to view progress.")
      );
      return dispose;
    }
    const header = el2("header", "osp-header");
    const heading = el2("div");
    heading.append(
      el2("p", "osp-eyebrow", "PROJECT WORKSPACE"),
      el2("h1", "", "OpenSpec progress"),
      el2("p", "osp-subtitle", "Planning artifacts and implementation checklists, directly from OpenSpec.")
    );
    const actions = el2("div", "osp-actions");
    const refresh = button("Refresh", "osp-button osp-primary", () => refreshData());
    actions.append(el2("span", "osp-readonly", "Manual actions"), refresh);
    header.append(heading, actions);
    const form = el2("form", "osp-project");
    const label = el2("label", "osp-field");
    label.append(el2("span", "osp-label", "Project directory"));
    const input = el2("input");
    input.type = "text";
    input.value = workspace;
    input.spellcheck = false;
    input.setAttribute("aria-label", "Project directory");
    input.autocomplete = "off";
    label.append(input);
    const load = el2("button", "osp-button", "Load project");
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
    const notice = el2("div", "osp-notice");
    notice.setAttribute("role", "status");
    notice.setAttribute("aria-live", "polite");
    const metrics = el2("div", "osp-metrics");
    const columns = el2("div", "osp-columns");
    const changePanel = el2("section", "osp-changes");
    const detailPanel = el2("section", "osp-detail");
    detailPanel.setAttribute("aria-label", "Change details");
    columns.append(changePanel, detailPanel);
    const footer = el2("footer", "osp-footer", "Task counts reflect OpenSpec checkboxes. They do not certify tests, review, or release readiness.");
    root.append(header, form, notice, metrics, columns, footer);
    const automationPanel = el2("div");
    root.insertBefore(automationPanel, metrics);
    disposeAutomation = mountAutomation({
      host,
      container: automationPanel,
      navigate,
      getWorkspace: () => snapshot?.workspace || "",
      getChange: () => requested?.[1] || snapshot?.changes[0]?.name || ""
    });
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
        const metric = el2("div", "osp-metric");
        metric.append(el2("span", "osp-label", labelText), el2("strong", "", value), el2("span", "osp-muted", hint));
        metrics.append(metric);
      }
      changePanel.replaceChildren(el2("h2", "osp-panel-title", "Active changes"));
      if (!changes.length) {
        changePanel.append(el2("p", "osp-empty", "No active changes. Create a proposal with your OpenSpec skill, then refresh."));
        return;
      }
      const list = el2("ul", "osp-change-list");
      for (const change of changes) {
        const item = el2("li");
        const link = el2("a", `osp-change${selected === change.name ? " osp-selected" : ""}`);
        link.href = `${base}/changes/${encodeURIComponent(change.name)}`;
        if (selected === change.name) link.setAttribute("aria-current", "page");
        link.addEventListener("click", (event) => {
          event.preventDefault();
          navigate(link.getAttribute("href"));
        });
        const state = change.totalTasks === 0 ? "No tasks yet" : change.completedTasks === change.totalTasks ? "Tasks complete" : "In progress";
        link.append(
          el2("strong", "osp-change-name", change.name),
          el2("span", "osp-muted", `${change.completedTasks} of ${change.totalTasks} tasks \xB7 ${state}`),
          progressBar(change.completedTasks, change.totalTasks, `${change.name} task progress`),
          el2("span", "osp-date", `Updated ${formatDate(change.lastModified)}`)
        );
        item.append(link);
        list.append(item);
      }
      changePanel.append(list);
    }
    function renderDetail() {
      detailPanel.replaceChildren();
      if (!detail) return;
      const head = el2("div", "osp-detail-header");
      const title = el2("div");
      title.append(el2("p", "osp-eyebrow", detail.schemaName), el2("h2", "", detail.name));
      head.append(title, el2(
        "span",
        `osp-badge ${detail.planningComplete ? "osp-done" : "osp-ready"}`,
        detail.planningComplete ? "Planning complete" : "Planning in progress"
      ));
      detailPanel.append(head, el2("h3", "osp-section-title", "Planning artifacts"));
      const artifacts = el2("ol", "osp-artifacts");
      for (const artifact of detail.artifacts) {
        const item = el2("li", "osp-artifact");
        const content = el2("div");
        content.append(el2("strong", "", artifact.id), el2("code", "osp-artifact-path", artifact.outputPath));
        if (artifact.requires.length) content.append(el2("span", "osp-date", `Requires ${artifact.requires.join(", ")}`));
        item.append(content, el2("span", `osp-badge osp-${artifact.status}`, STATE_LABELS[artifact.status]));
        artifacts.append(item);
      }
      detailPanel.append(artifacts);
      const taskHeader = el2("div", "osp-task-header");
      taskHeader.append(el2("h3", "osp-section-title", "Implementation tasks"));
      if (detail.progress) taskHeader.append(el2("span", "osp-muted", `${detail.progress.complete} / ${detail.progress.total} checked`));
      detailPanel.append(taskHeader);
      if (detail.progress === null) {
        detailPanel.append(el2("p", "osp-empty", detail.taskError || detail.instruction || "Task progress is not available yet. Complete the planning artifacts first."));
      } else if (!detail.tasks.length) {
        detailPanel.append(el2("p", "osp-empty", "No tasks are tracked for this change."));
      } else {
        if (detail.tasks.length < detail.progress.total) {
          detailPanel.append(el2("p", "osp-muted", "Only available task descriptions are listed below."));
        }
        const tasks = el2("ul", "osp-tasks");
        for (const task of detail.tasks) {
          const item = el2("li", "osp-task");
          const mark = el2("span", task.done ? "osp-check osp-checked" : "osp-check", task.done ? "\u2713" : "\u25CB");
          mark.setAttribute("aria-label", task.done ? "Complete" : "Remaining");
          const text = el2("div");
          text.append(el2("span", "", task.description));
          const relative = task.sourcePath.startsWith(snapshot.workspace + "/") ? task.sourcePath.slice(snapshot.workspace.length + 1) : task.sourcePath;
          text.append(el2("code", "osp-task-source", `${relative}:${task.line}`));
          item.append(mark, text);
          tasks.append(item);
        }
        detailPanel.append(tasks);
      }
      const next = el2("div", "osp-next");
      const nextText = !detail.planningComplete ? "Continue planning in an OpenHands conversation." : detail.progress === null ? "Resolve the task-tracking issue before starting implementation." : detail.progress.remaining ? "Continue Apply after reviewing the planning artifacts." : "Review implementation and verification evidence before syncing or archiving.";
      next.append(el2("strong", "", "Next human decision"), el2("p", "", nextText));
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
      if (!snapshot) detailPanel.replaceChildren(el2("p", "osp-empty", "Loading project progress\u2026"));
      try {
        const overview = await loadOverview(host, workspace);
        if (!current()) return;
        snapshot = overview;
        overviewUpdated = true;
        detail = null;
        const selected = requested?.[1] || overview.changes[0]?.name;
        renderOverview(selected);
        if (!selected) {
          detailPanel.replaceChildren(el2("div", "osp-empty", "Your active change details will appear here."));
        } else if (!overview.changes.some((change) => change.name === selected)) {
          detailPanel.replaceChildren(
            el2("h2", "", "Change not found"),
            el2("p", "osp-empty", "This change may have been archived or removed. Choose another active change.")
          );
        } else {
          detailPanel.replaceChildren(el2("p", "osp-empty", `Loading ${selected}\u2026`));
          try {
            const change = await loadChange(host, workspace, selected);
            if (!current()) return;
            detail = change;
            renderDetail();
          } catch (error) {
            if (!current()) return;
            detailPanel.replaceChildren(el2("h2", "", selected), el2("p", "osp-error", error.message));
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
