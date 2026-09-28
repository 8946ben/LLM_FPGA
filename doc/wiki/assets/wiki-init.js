/* LLM_FPGA 项目图wiki 公共脚本：全站统一的 Mermaid 初始化。
 * securityLevel 必须为 loose，flowchart 的 click 节点跳转才会生效。
 */
(function () {
  function boot() {
    if (typeof mermaid === 'undefined') {
      document.querySelectorAll('figure.diagram').forEach(function (fig) {
        var tip = document.createElement('p');
        tip.className = 'note warn';
        tip.textContent = '未找到 assets/mermaid.min.js，图无法渲染。';
        fig.appendChild(tip);
      });
      return;
    }

    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'loose',
      theme: 'base',
      fontFamily:
        '-apple-system, "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif',
      themeVariables: {
        fontSize: '14px',
        primaryColor: '#eaf3ff',
        primaryTextColor: '#1f2328',
        primaryBorderColor: '#8ab4f8',
        secondaryColor: '#f2f4f7',
        tertiaryColor: '#ffffff',
        lineColor: '#59636e',
        textColor: '#1f2328',
        clusterBkg: '#fbfcfd',
        clusterBorder: '#c6d0da',
        edgeLabelBackground: '#ffffff',
        noteBkgColor: '#fff8e5',
        noteBorderColor: '#e6c34a'
      },
      flowchart: { curve: 'basis', htmlLabels: true, useMaxWidth: true, padding: 12 },
      sequence: { useMaxWidth: true, wrap: true },
      state: { useMaxWidth: true },
      gantt: { useMaxWidth: true, fontSize: 13 }
    });

    mermaid.run({ querySelector: '.mermaid' }).catch(function (err) {
      console.error('[wiki] mermaid render failed', err);
      document.querySelectorAll('figure.diagram').forEach(function (fig) {
        var tip = document.createElement('p');
        tip.className = 'note warn';
        tip.textContent = '图渲染失败，请查看浏览器控制台：' + err.message;
        fig.appendChild(tip);
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
