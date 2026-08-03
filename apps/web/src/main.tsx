import { StrictMode, Component, type ErrorInfo, type ReactNode } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import App from './App';
import './styles.css';
import './stage.css';
import './panel.css';

/* Top-level boundary. A render crash must not leave a blank page: the whole
   point of the offline demo is that it degrades to something a presenter can
   still talk from. */
class Boundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  override state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  override componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[sparc] unhandled render error', error, info.componentStack);
  }
  override render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="callout callout--stop" role="alert">
        <p className="callout__title">The panel failed to render</p>
        <div className="callout__body">
          <p>{this.state.error.message}</p>
          <p>The underlying results are immutable JSON under <code>contracts/examples/</code>.</p>
        </div>
      </div>
    );
  }
}

/* ── panel API ───────────────────────────────────────────────────────────────
   The globe is a build-free ES-module page; it cannot import React. So this
   bundle publishes a tiny imperative surface on `window.SPARC` and the globe
   calls it. Two entry paths, one component:

     · standalone at /app/  — full-page dashboard, root already in the HTML
     · panel over the globe — mounted on demand into a fixed side drawer

   Mounting lazily matters: opening the panel is the first moment the analytics
   are needed, and until then the globe should not pay for a React tree. */
export interface PanelTarget { lat: number; lon: number; name: string }

let panelRoot: Root | null = null;
let panelHost: HTMLElement | null = null;

function ensureHost(): HTMLElement {
  if (panelHost) return panelHost;
  const el = document.createElement('aside');
  el.id = 'sparc-panel';
  el.className = 'sparc-panel';
  el.setAttribute('aria-label', 'SPARC district analysis');
  document.body.appendChild(el);
  panelHost = el;
  return el;
}

function openPanel(target: PanelTarget) {
  const host = ensureHost();
  host.classList.add('sparc-panel--open');
  document.documentElement.classList.add('sparc-panel-open');
  if (!panelRoot) panelRoot = createRoot(host);
  panelRoot.render(
    <StrictMode>
      <Boundary>
        <App panel={{ target, onClose: closePanel }} />
      </Boundary>
    </StrictMode>,
  );
  // Move focus in, or a keyboard user is left behind on the globe.
  requestAnimationFrame(() => host.querySelector<HTMLElement>('[data-autofocus]')?.focus());
}

function closePanel() {
  panelHost?.classList.remove('sparc-panel--open');
  document.documentElement.classList.remove('sparc-panel-open');
}

declare global {
  interface Window {
    SPARC?: { open: (t: PanelTarget) => void; close: () => void };
  }
}
window.SPARC = { open: openPanel, close: closePanel };

/* Standalone route: /app/ still renders the dashboard on its own. */
const standalone = document.getElementById('root');
if (standalone) {
  createRoot(standalone).render(
    <StrictMode><Boundary><App /></Boundary></StrictMode>,
  );
}
