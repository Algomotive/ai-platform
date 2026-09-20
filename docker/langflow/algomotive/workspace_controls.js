(() => {
  const CONTROL_ID = 'algomotive-workflow-signout';
  const BRAND_ID = 'algomotive-workflow-brand';
  const STYLE_ID = 'algomotive-workflow-shell-style';

  const normalizedText = (element) =>
    (element?.textContent || '').replace(/\s+/g, ' ').trim();

  const hideClosestControl = (element) => {
    const control = element?.closest(
      'a, button, [role="button"], li, [data-radix-collection-item]'
    );
    if (control) {
      control.style.display = 'none';
      control.setAttribute('aria-hidden', 'true');
    } else if (element) {
      element.style.display = 'none';
      element.setAttribute('aria-hidden', 'true');
    }
  };

  const applyAlgomotiveTerminology = () => {
    const terminology = new Map([
      ['Langflow Assistant', 'AlgoFlow Assistant'],
      [
        'Manage the general settings for Langflow.',
        'Manage the general settings for AlgoFlow.'
      ],
      [
        'Manage settings related to Langflow and your account.',
        'Manage settings related to AlgoFlow and your account.'
      ],
      [
        'Choose the display language for the Langflow interface.',
        'Choose the display language for the AlgoFlow interface.'
      ],
      ['Langflow API Keys', 'AlgoFlow API Keys'],
      ['Langflow MCP Client', 'AlgoFlow MCP Client'],
      [
        'Your secret Langflow API keys are listed below. Do not share your API key with others, or expose it in the browser or other client-side code.',
        'Your secret AlgoFlow API keys are listed below. Do not share your API key with others, or expose it in the browser or other client-side code.'
      ]
    ]);

    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT
    );

    const replacements = [];

    while (walker.nextNode()) {
      const node = walker.currentNode;
      const value = node.nodeValue?.trim();

      if (value && terminology.has(value)) {
        replacements.push([node, terminology.get(value)]);
      }
    }

    replacements.forEach(([node, value]) => {
      node.nodeValue = value;
    });
  };

  const applyAlgoFlowAssistantArtwork = () => {
    const textNodes = [];
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT
    );

    while (walker.nextNode()) {
      if (walker.currentNode.nodeValue?.trim() === 'AlgoFlow Assistant') {
        textNodes.push(walker.currentNode);
      }
    }

    textNodes.forEach((titleNode) => {
      const panel = titleNode.parentElement?.closest(
        '[role="dialog"], [data-radix-dialog-content], .fixed, .absolute'
      );

      if (!panel || panel.dataset.algomotiveAssistantArtwork === 'true') {
        return;
      }

      const providerNode = Array.from(
        panel.querySelectorAll('h1, h2, h3, p, span, div')
      ).find(
        (element) =>
          normalizedText(element) === 'No Model Provider Configured'
      );

      if (!providerNode) {
        return;
      }

      const candidates = Array.from(
        panel.querySelectorAll('img, svg')
      ).filter((element) => {
        const rectangle = element.getBoundingClientRect();
        return rectangle.width >= 28 && rectangle.height >= 28;
      });

      const upstreamArtwork = candidates.find((element) => {
        const rectangle = element.getBoundingClientRect();
        const providerRectangle = providerNode.getBoundingClientRect();

        return (
          rectangle.bottom <= providerRectangle.top &&
          providerRectangle.top - rectangle.bottom < 180
        );
      });

      if (!upstreamArtwork) {
        return;
      }

      const container = upstreamArtwork.parentElement;
      if (!container) {
        return;
      }

      upstreamArtwork.style.display = 'none';
      upstreamArtwork.setAttribute('aria-hidden', 'true');

      const mark = document.createElement('img');
      mark.src = '/assets/algomotive-mark.svg';
      mark.alt = 'Algomotive';
      mark.className = 'algomotive-assistant-mark';

      Object.assign(mark.style, {
        width: '48px',
        height: '48px',
        objectFit: 'contain',
        display: 'block',
        margin: '0 auto'
      });

      container.appendChild(mark);
      panel.dataset.algomotiveAssistantArtwork = 'true';
    });
  };

  const removeUpstreamPromotions = () => {
    const exactTextTargets = new Set([
      'Star repo for updates',
      'Join the community',
      '155k',
      '25k'
    ]);

    document.querySelectorAll('a, button, span, p, div').forEach((element) => {
      const text = normalizedText(element);

      if (exactTextTargets.has(text)) {
        hideClosestControl(element);
      }
    });

    document.querySelectorAll('a[href]').forEach((anchor) => {
      const href = anchor.getAttribute('href') || '';

      if (
        href.includes('github.com/langflow-ai') ||
        href.includes('discord.gg')
      ) {
        anchor.style.display = 'none';
        anchor.setAttribute('aria-hidden', 'true');
      }
    });

    document.querySelectorAll('span, p, div').forEach((element) => {
      if (normalizedText(element) === 'Create a flow') {
        element.textContent = 'Create a workflow';
      }
    });
  };

  const installStyle = () => {
    if (document.getElementById(STYLE_ID)) {
      return;
    }

    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      #${BRAND_ID} {
        position: fixed;
        top: 0;
        left: 0;
        z-index: 2147483000;
        display: inline-flex;
        align-items: center;
        justify-content: flex-start;
        gap: 10px;
        width: 430px;
        box-sizing: border-box;
        height: 54px;
        padding: 0 20px;
        border: 0;
        border-radius: 0;
        background: rgba(255, 255, 255, 0.99);
        color: #0f3640;
        box-shadow: none;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        pointer-events: none;
      }

      #${BRAND_ID} img {
        width: 172px;
        height: 29px;
        object-fit: contain;
        object-position: left center;
      }

      #${BRAND_ID} .algomotive-brand-divider {
        width: 1px;
        height: 21px;
        background: rgba(15, 54, 64, 0.18);
      }

      #${BRAND_ID} .algomotive-product-label {
        font-family: inherit;
        font-size: 13px;
        font-weight: 650;
        line-height: 1;
        letter-spacing: 0.025em;
        color: rgba(15, 54, 64, 0.72);
        white-space: nowrap;
      }

      #${CONTROL_ID} {
        position: fixed;
        top: 9px;
        right: 68px;
        z-index: 2147483000;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 7px;
        height: 36px;
        padding: 0 12px 0 9px;
        border: 1px solid rgba(15, 54, 64, 0.11);
        border-radius: 12px;
        background: rgba(247, 250, 249, 0.97);
        color: #0f3640;
        box-shadow: 0 1px 3px rgba(15, 54, 64, 0.06);
        font-family: inherit;
        font-size: 12.5px;
        font-weight: 650;
        line-height: 1;
        text-decoration: none;
        cursor: pointer;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        transition:
          background-color 140ms ease,
          border-color 140ms ease,
          box-shadow 140ms ease,
          transform 140ms ease;
      }

      #${CONTROL_ID}:hover {
        background: #edf8f5;
        border-color: rgba(22, 166, 148, 0.32);
        box-shadow: 0 2px 6px rgba(15, 54, 64, 0.09);
        transform: translateY(-1px);
      }

      #${CONTROL_ID}:focus-visible {
        outline: 2px solid rgba(22, 166, 148, 0.55);
        outline-offset: 2px;
      }

      #${CONTROL_ID} .algomotive-signout-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 19px;
        height: 19px;
        border-radius: 7px;
        background: rgba(22, 166, 148, 0.12);
        color: #118b7d;
        font-size: 14px;
        font-weight: 700;
      }

      @media (max-width: 760px) {
        #${BRAND_ID} .algomotive-brand-divider,
        #${BRAND_ID} .algomotive-product-label,
        #${CONTROL_ID} .algomotive-signout-label {
          display: none;
        }

        #${BRAND_ID} img {
          width: 138px;
        }

        #${CONTROL_ID} {
          width: 36px;
          min-width: 36px;
          padding: 0;
        }
      }
    `;

    document.head.appendChild(style);
  };

  const installBrand = () => {
    if (document.getElementById(BRAND_ID)) {
      return;
    }

    const brand = document.createElement('div');
    brand.id = BRAND_ID;
    brand.setAttribute('aria-label', 'Algomotive Workflow Studio');

    const wordmark = document.createElement('img');
    wordmark.src = '/assets/algomotive-wordmark-dark.svg';
    wordmark.alt = 'Algomotive';

    const divider = document.createElement('span');
    divider.className = 'algomotive-brand-divider';
    divider.setAttribute('aria-hidden', 'true');

    const label = document.createElement('span');
    label.className = 'algomotive-product-label';
    label.textContent = 'Workflow Studio';

    brand.append(wordmark, divider, label);
    document.body.appendChild(brand);
  };

  const applyAlgoFlowRouteLoadingOverlay = () => {
    const overlayId = 'algomotive-route-loading-overlay';

    const loadingVisible = Array.from(
      document.querySelectorAll('body *')
    ).some((element) => {
      return (
        element.children.length === 0 &&
        normalizedText(element) === 'Loading...'
      );
    });

    let overlay = document.getElementById(overlayId);

    if (loadingVisible && !overlay) {
      overlay = document.createElement('div');
      overlay.id = overlayId;
      overlay.setAttribute(
        'aria-label',
        'Loading AlgoFlow workflow'
      );

      Object.assign(overlay.style, {
        position: 'fixed',
        top: '54px',
        right: '0',
        bottom: '0',
        left: '380px',
        zIndex: '2147482500',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(255, 255, 255, 0.985)',
        opacity: '0',
        transition: 'opacity 140ms ease',
        pointerEvents: 'none'
      });

      const content = document.createElement('div');

      Object.assign(content.style, {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '18px'
      });

      const mark = document.createElement('img');
      mark.src = '/assets/algomotive-mark.svg';
      mark.alt = 'Algomotive';

      Object.assign(mark.style, {
        width: '76px',
        height: '76px',
        display: 'block',
        objectFit: 'contain'
      });

      const label = document.createElement('div');
      label.textContent = 'Loading AlgoFlow...';

      Object.assign(label.style, {
        color: '#0f3640',
        fontFamily: 'inherit',
        fontSize: '16px',
        fontWeight: '600',
        letterSpacing: '0.01em'
      });

      content.append(mark, label);
      overlay.appendChild(content);
      document.body.appendChild(overlay);

      window.requestAnimationFrame(() => {
        if (overlay) {
          overlay.style.opacity = '1';
        }
      });
    }

    if (!loadingVisible && overlay) {
      overlay.style.opacity = '0';

      window.setTimeout(() => {
        if (overlay && overlay.parentNode) {
          overlay.parentNode.removeChild(overlay);
        }
      }, 180);
    }
  };

  const applyAlgomotiveDefaultAvatar = () => {
    const viewportWidth = window.innerWidth;

    document.querySelectorAll('img').forEach((image) => {
      const rectangle = image.getBoundingClientRect();

      if (
        rectangle.top >= 0 &&
        rectangle.top < 70 &&
        rectangle.right > viewportWidth - 90 &&
        rectangle.width >= 24 &&
        rectangle.width <= 56 &&
        rectangle.height >= 24 &&
        rectangle.height <= 56 &&
        !image.closest('#algomotive-workflow-brand')
      ) {
        if (image.dataset.algomotiveAccountAvatar === 'true') {
          return;
        }

        image.src = '/assets/algomotive-mark.svg';
        image.alt = 'Algomotive account';
        image.dataset.algomotiveAccountAvatar = 'true';
        image.style.objectFit = 'contain';
        image.style.padding = '4px';
        image.style.background = '#f7faf9';
      }
    });
  };

  const applyAlgomotiveCanvasToolbarIdentity = () => {
    const zoomLabels = Array.from(
      document.querySelectorAll('span, div, button')
    ).filter((element) => /^\d+%$/.test(normalizedText(element)));

    zoomLabels.forEach((zoomLabel) => {
      const toolbar = zoomLabel.closest(
        '[role="toolbar"], [class*="toolbar"], [class*="Toolbar"]'
      ) || zoomLabel.parentElement?.parentElement;

      if (!toolbar) {
        return;
      }

      const buttons = Array.from(
        toolbar.querySelectorAll('button, [role="button"]')
      );

      const zoomRectangle = zoomLabel.getBoundingClientRect();

      const identityButton = buttons
        .filter((button) => {
          const rectangle = button.getBoundingClientRect();

          return (
            rectangle.right <= zoomRectangle.left &&
            zoomRectangle.left - rectangle.right < 90 &&
            rectangle.width >= 32 &&
            rectangle.width <= 72 &&
            rectangle.height >= 32 &&
            rectangle.height <= 72
          );
        })
        .sort(
          (first, second) =>
            second.getBoundingClientRect().right -
            first.getBoundingClientRect().right
        )[0];

      if (
        !identityButton ||
        identityButton.dataset.algomotiveCanvasIdentity === 'true'
      ) {
        return;
      }

      identityButton.dataset.algomotiveCanvasIdentity = 'true';
      identityButton.setAttribute(
        'aria-label',
        identityButton.getAttribute('aria-label') ||
          'Algomotive canvas control'
      );

      identityButton.querySelectorAll('svg, img').forEach((artwork) => {
        artwork.style.opacity = '0';
        artwork.style.pointerEvents = 'none';
      });

      Object.assign(identityButton.style, {
        backgroundColor: '#f2faf8',
        backgroundImage: "url('/assets/algomotive-mark.svg')",
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundSize: '27px 27px',
        borderColor: 'rgba(15, 54, 64, 0.10)',
        boxShadow: 'inset 0 0 0 1px rgba(22, 166, 148, 0.06)'
      });
    });
  };

  const installSignOut = () => {
    if (document.getElementById(CONTROL_ID)) {
      return;
    }

    const control = document.createElement('button');
    control.id = CONTROL_ID;
    control.type = 'button';
    control.setAttribute(
      'aria-label',
      'Sign out of Algomotive Workflow Studio'
    );
    control.setAttribute('title', 'Sign out');

    const icon = document.createElement('span');
    icon.className = 'algomotive-signout-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = '↪';

    const label = document.createElement('span');
    label.className = 'algomotive-signout-label';
    label.textContent = 'Sign out';

    control.append(icon, label);

    control.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      window.location.assign(window.location.origin + '/logout');
    });

    document.body.appendChild(control);
  };

  const applyUniformShell = () => {
    installStyle();
    installBrand();
    installSignOut();
    removeUpstreamPromotions();
    applyAlgomotiveTerminology();
    applyAlgoFlowAssistantArtwork();
    applyAlgoFlowRouteLoadingOverlay();
    applyAlgomotiveDefaultAvatar();
    applyAlgomotiveCanvasToolbarIdentity();
  };

  const start = () => {
    applyUniformShell();

    const observer = new MutationObserver(() => {
      applyUniformShell();
    });

    observer.observe(document.documentElement, {
      childList: true,
      subtree: true
    });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }
})();
