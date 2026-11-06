/* LLM_FPGA 项目图wiki 公共脚本
 *
 * 1. 统一初始化 Mermaid（securityLevel: loose 才能让 flowchart 的 click 跳转生效）。
 * 2. 把每张图包成「画布」：SVG 按自然尺寸渲染（useMaxWidth: false），
 *    由视口提供滚轮缩放、拖拽平移与缩放按钮，保证大图字号不被压缩。
 */
(function () {
  'use strict';

  var MIN_SCALE = 0.15;
  var MAX_SCALE = 8;
  var ZOOM_STEP = 1.25;
  var DRAG_THRESHOLD = 6;

  /* ---------------- 画布 ---------------- */

  function naturalSize(svg) {
    var viewBox = svg.getAttribute('viewBox');
    if (viewBox) {
      var parts = viewBox.split(/[\s,]+/).map(Number);
      if (parts.length === 4 && parts[2] > 0 && parts[3] > 0) {
        return { w: parts[2], h: parts[3] };
      }
    }
    var box = svg.getBoundingClientRect();
    return { w: Math.max(box.width, 1), h: Math.max(box.height, 1) };
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function createCanvas(figure) {
    if (figure.dataset.canvasReady === '1') return;

    // 支持两类图：Mermaid 渲染结果，以及页面内直接内联的示意图 SVG
    var mermaidDiv = figure.querySelector('.mermaid');
    var svg = mermaidDiv
      ? mermaidDiv.querySelector('svg')
      : figure.querySelector('svg.schematic');
    if (!svg) return;
    figure.dataset.canvasReady = '1';

    if (!mermaidDiv) {
      mermaidDiv = document.createElement('div');
      mermaidDiv.className = 'mermaid';
      svg.parentNode.insertBefore(mermaidDiv, svg);
      mermaidDiv.appendChild(svg);
    }

    // SVG 按自然尺寸渲染，不再被容器宽度压缩
    var size = naturalSize(svg);
    svg.removeAttribute('style');
    svg.setAttribute('width', size.w);
    svg.setAttribute('height', size.h);
    svg.style.display = 'block';
    svg.style.maxWidth = 'none';

    var toolbar = document.createElement('div');
    toolbar.className = 'canvas-toolbar';
    toolbar.innerHTML =
      '<button type="button" data-act="out" title="缩小" aria-label="缩小">&#8722;</button>' +
      '<span class="zoom-readout" aria-live="polite">100%</span>' +
      '<button type="button" data-act="in" title="放大" aria-label="放大">+</button>' +
      '<span class="toolbar-sep" role="separator"></span>' +
      '<button type="button" data-act="fit-width">适应宽度</button>' +
      '<button type="button" data-act="fit-all">适应窗口</button>' +
      '<button type="button" data-act="one">1:1</button>' +
      '<span class="toolbar-hint">滚轮缩放 &#183; 拖拽平移 &#183; 双击复位</span>';

    var viewport = document.createElement('div');
    viewport.className = 'canvas-viewport';
    viewport.tabIndex = 0;

    var stage = document.createElement('div');
    stage.className = 'canvas-stage';

    figure.insertBefore(toolbar, mermaidDiv);
    figure.insertBefore(viewport, mermaidDiv);
    viewport.appendChild(stage);
    stage.appendChild(mermaidDiv);
    mermaidDiv.classList.add('canvas-body');

    var readout = toolbar.querySelector('.zoom-readout');
    var scale = 1;
    var offsetX = 0;
    var offsetY = 0;
    var userAdjusted = false;

    function viewportSize() {
      return { w: viewport.clientWidth || 1, h: viewport.clientHeight || 1 };
    }

    function render() {
      stage.style.transform =
        'translate(' + offsetX + 'px,' + offsetY + 'px) scale(' + scale + ')';
      readout.textContent = Math.round(scale * 100) + '%';
    }

    /* 让图在视口内居中；比视口大的方向贴左上，便于从左读起 */
    function centerView() {
      var view = viewportSize();
      var scaledW = size.w * scale;
      var scaledH = size.h * scale;
      offsetX = scaledW > view.w ? 0 : (view.w - scaledW) / 2;
      offsetY = scaledH > view.h ? 0 : (view.h - scaledH) / 2;
      render();
    }

    function zoomTo(nextScale, anchorX, anchorY) {
      nextScale = clamp(nextScale, MIN_SCALE, MAX_SCALE);
      if (Math.abs(nextScale - scale) < 1e-6) return;
      var view = viewportSize();
      if (anchorX === undefined) {
        anchorX = view.w / 2;
        anchorY = view.h / 2;
      }
      var ratio = nextScale / scale;
      offsetX = anchorX - (anchorX - offsetX) * ratio;
      offsetY = anchorY - (anchorY - offsetY) * ratio;
      scale = nextScale;
      userAdjusted = true;
      render();
    }

    function fitWidth() {
      var view = viewportSize();
      scale = clamp(view.w / size.w, MIN_SCALE, MAX_SCALE);
      var scaledH = size.h * scale;
      offsetX = 0;
      offsetY = scaledH > view.h ? 0 : (view.h - scaledH) / 2;
      userAdjusted = true;
      render();
    }

    function fitAll() {
      var view = viewportSize();
      scale = clamp(Math.min(view.w / size.w, view.h / size.h), MIN_SCALE, MAX_SCALE);
      userAdjusted = true;
      centerView();
    }

    /* 视口高度：随图实际高度自适应，并受窗口高度约束 */
    function resizeViewport() {
      var cap = Math.round(window.innerHeight * 0.75);
      var wanted = size.h + 8;
      viewport.style.height = Math.round(clamp(wanted, 220, Math.max(cap, 260))) + 'px';
    }

    /* --- 工具栏 --- */
    toolbar.addEventListener('click', function (event) {
      var button = event.target.closest('button[data-act]');
      if (!button) return;
      switch (button.dataset.act) {
        case 'in':
          zoomTo(scale * ZOOM_STEP);
          break;
        case 'out':
          zoomTo(scale / ZOOM_STEP);
          break;
        case 'fit-width':
          fitWidth();
          break;
        case 'fit-all':
          fitAll();
          break;
        case 'one':
          scale = 1;
          userAdjusted = true;
          centerView();
          break;
      }
    });

    /* --- 滚轮缩放（以指针位置为锚点） --- */
    viewport.addEventListener(
      'wheel',
      function (event) {
        event.preventDefault();
        var rect = viewport.getBoundingClientRect();
        var factor = event.deltaY < 0 ? 1.12 : 1 / 1.12;
        zoomTo(scale * factor, event.clientX - rect.left, event.clientY - rect.top);
      },
      { passive: false }
    );

    /* --- 拖拽平移 --- */
    var dragging = false;
    var lastX = 0;
    var lastY = 0;
    var traveled = 0;
    var suppressNextClick = false;

    viewport.addEventListener('pointerdown', function (event) {
      if (event.button !== 0) return;
      dragging = true;
      traveled = 0;
      lastX = event.clientX;
      lastY = event.clientY;
      viewport.classList.add('dragging');
      if (viewport.setPointerCapture) {
        try {
          viewport.setPointerCapture(event.pointerId);
        } catch (err) {
          /* 忽略：部分环境不支持捕获 */
        }
      }
    });

    viewport.addEventListener('pointermove', function (event) {
      if (!dragging) return;
      var dx = event.clientX - lastX;
      var dy = event.clientY - lastY;
      lastX = event.clientX;
      lastY = event.clientY;
      traveled += Math.abs(dx) + Math.abs(dy);
      offsetX += dx;
      offsetY += dy;
      userAdjusted = true;
      render();
    });

    function endDrag(event) {
      if (!dragging) return;
      dragging = false;
      viewport.classList.remove('dragging');
      // 拖拽结束后抑制一次 click，避免误触发图内节点跳转
      suppressNextClick = traveled > DRAG_THRESHOLD;
      if (viewport.releasePointerCapture) {
        try {
          viewport.releasePointerCapture(event.pointerId);
        } catch (err) {
          /* 忽略 */
        }
      }
    }

    viewport.addEventListener('pointerup', endDrag);
    viewport.addEventListener('pointercancel', endDrag);

    viewport.addEventListener(
      'click',
      function (event) {
        if (!suppressNextClick) return;
        suppressNextClick = false;
        event.preventDefault();
        event.stopPropagation();
      },
      true
    );

    viewport.addEventListener('dblclick', function () {
      scale = 1;
      userAdjusted = false;
      centerView();
    });

    /* --- 键盘操作 --- */
    viewport.addEventListener('keydown', function (event) {
      var handled = true;
      switch (event.key) {
        case '+':
        case '=':
          zoomTo(scale * ZOOM_STEP);
          break;
        case '-':
        case '_':
          zoomTo(scale / ZOOM_STEP);
          break;
        case '0':
          scale = 1;
          userAdjusted = true;
          centerView();
          break;
        case 'ArrowLeft':
          offsetX += 40;
          render();
          break;
        case 'ArrowRight':
          offsetX -= 40;
          render();
          break;
        case 'ArrowUp':
          offsetY += 40;
          render();
          break;
        case 'ArrowDown':
          offsetY -= 40;
          render();
          break;
        default:
          handled = false;
      }
      if (handled) event.preventDefault();
    });

    window.addEventListener('resize', function () {
      if (userAdjusted) return;
      resizeViewport();
      centerView();
    });

    resizeViewport();
    centerView();
  }

  function attachAll() {
    document.querySelectorAll('figure.diagram').forEach(createCanvas);
  }

  /* ---------------- Mermaid ---------------- */

  function showNotice(message, isError) {
    document.querySelectorAll('figure.diagram').forEach(function (figure) {
      var tip = document.createElement('p');
      tip.className = 'note' + (isError ? ' warn' : '');
      tip.textContent = message;
      figure.appendChild(tip);
    });
  }

  function boot() {
    if (typeof mermaid === 'undefined') {
      showNotice('未找到 assets/mermaid.min.js，图无法渲染。', true);
      return;
    }

    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'loose',
      theme: 'base',
      fontFamily:
        '-apple-system, "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif',
      themeVariables: {
        fontSize: '16px',
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
      // useMaxWidth 必须为 false：由画布接管缩放，避免大图被压小导致字号不可读
      flowchart: {
        curve: 'basis',
        htmlLabels: true,
        useMaxWidth: false,
        padding: 14,
        nodeSpacing: 45,
        rankSpacing: 55
      },
      sequence: { useMaxWidth: false, wrap: true, messageFontSize: 15, actorFontSize: 15 },
      state: { useMaxWidth: false, fontSize: 15 },
      gantt: { useMaxWidth: false, fontSize: 15, barHeight: 22, topPadding: 55 }
    });

    mermaid
      .run({ querySelector: '.mermaid' })
      .then(attachAll)
      .catch(function (err) {
        console.error('[wiki] mermaid render failed', err);
        showNotice('图渲染失败，请查看浏览器控制台：' + err.message, true);
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  // 暴露给调试与自动化测试使用
  window.WikiCanvas = { attachAll: attachAll, createCanvas: createCanvas };
})();
