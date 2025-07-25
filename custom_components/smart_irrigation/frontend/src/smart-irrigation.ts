import { LitElement, html, CSSResultGroup, css } from "lit";
import { property, customElement } from "lit/decorators.js";
import { HomeAssistant, navigate } from "custom-card-helpers";
import { loadHaForm } from "./load-ha-elements";

import "./views/general/view-general.ts";
import "./views/zones/view-zones.ts";
import "./views/modules/view-modules.ts";
import "./views/mappings/view-mappings.ts";
import "./views/info/view-info.ts";

import { commonStyle } from "./styles";
import { VERSION, PLATFORM } from "./const";
import { localize } from "../localize/localize";
import { exportPath, getPath, Path } from "./common/navigation";

@customElement("smart-irrigation")
export class SmartIrrigationPanel extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property({ type: Boolean, reflect: true }) public narrow!: boolean;

  private _updateScheduled = false;
  private _lastNavigationTime = 0;
  private _navigationThrottleDelay = 100; // Prevent too rapid navigation updates

  private _scheduleUpdate() {
    if (this._updateScheduled) return;
    this._updateScheduled = true;
    requestAnimationFrame(() => {
      this._updateScheduled = false;
      this.requestUpdate();
    });
  }

  async firstUpdated() {
    window.addEventListener("location-changed", () => {
      if (!window.location.pathname.includes(PLATFORM)) return;

      // Throttle navigation updates to prevent browser throttling
      const now = performance.now();
      if (now - this._lastNavigationTime < this._navigationThrottleDelay) {
        return; // Skip this update if too soon
      }
      this._lastNavigationTime = now;

      this._scheduleUpdate();
    });

    // Load HA form elements in background without blocking initial render
    loadHaForm()
      .then(() => {
        // Trigger re-render once HA elements are loaded for better UX
        this._scheduleUpdate();
      })
      .catch((error) => {
        console.error("Failed to load HA form elements:", error);
        // Still trigger update to show whatever we can
        this._scheduleUpdate();
      });
  }

  render() {
    // Remove the blocking check - let the app render even if HA elements aren't fully loaded
    const path = getPath();
    return html`
      <div class="header">
        <div class="toolbar">
          <ha-menu-button
            .hass=${this.hass}
            .narrow=${this.narrow}
          ></ha-menu-button>
          <div class="main-title">${localize("title", this.hass.language)}</div>
          <div class="version">${VERSION}</div>
        </div>

        <sl-tab-group
          scrollable
          attr-for-selected="page-name"
          .selected=${path.page}
          @sl-tab-show=${this.handlePageSelected}
        >
          <sl-tab slot="nav" panel="info" .active=${path.page === "info"}>
            ${localize("panels.info.title", this.hass.language)}
          </sl-tab>
          <sl-tab slot="nav" panel="general" .active=${path.page === "general"}>
            ${localize("panels.general.title", this.hass.language)}
          </sl-tab>
          <sl-tab slot="nav" panel="zones" .active=${path.page === "zones"}>
            ${localize("panels.zones.title", this.hass.language)}
          </sl-tab>
          <sl-tab slot="nav" panel="modules" .active=${path.page === "modules"}>
            ${localize("panels.modules.title", this.hass.language)}
          </sl-tab>
          <sl-tab
            slot="nav"
            panel="mappings"
            .active=${path.page === "mappings"}
          >
            ${localize("panels.mappings.title", this.hass.language)}
          </sl-tab>
          <sl-tab slot="nav" panel="help" .active=${path.page === "help"}>
            ${localize("panels.help.title", this.hass.language)}
          </sl-tab>
        </sl-tab-group>
      </div>
      <div class="view">${this.getView(path)}</div>
    `;
  }

  getView(path: Path) {
    const page = path.page;
    switch (page) {
      case "info":
        return html`
          <smart-irrigation-view-info
            .hass=${this.hass}
            .narrow=${this.narrow}
            .path=${path}
          ></smart-irrigation-view-info>
        `;
      case "general":
        return html`
          <smart-irrigation-view-general
            .hass=${this.hass}
            .narrow=${this.narrow}
            .path=${path}
          ></smart-irrigation-view-general>
        `;
      case "zones":
        return html`
          <smart-irrigation-view-zones
            .hass=${this.hass}
            .narrow=${this.narrow}
            .path=${path}
          ></smart-irrigation-view-zones>
        `;
      case "modules":
        return html`
          <smart-irrigation-view-modules
            .hass=${this.hass}
            .narrow=${this.narrow}
            .path=${path}
          ></smart-irrigation-view-modules>
        `;
      case "mappings":
        return html`
          <smart-irrigation-view-mappings
            .hass=${this.hass}
            .narrow=${this.narrow}
            .path=${path}
          ></smart-irrigation-view-mappings>
        `;
      case "help":
        return html`<ha-card
          header="${localize(
            "panels.help.cards.how-to-get-help.title",
            this.hass.language,
          )}"
        >
          <div class="card-content">
            ${localize(
              "panels.help.cards.how-to-get-help.first-read-the",
              this.hass.language,
            )}
            <a href="https://github.com/jeroenterheerdt/HAsmartirrigation/wiki"
              >${localize(
                "panels.help.cards.how-to-get-help.wiki",
                this.hass.language,
              )}</a
            >.
            ${localize(
              "panels.help.cards.how-to-get-help.if-you-still-need-help",
              this.hass.language,
            )}
            <a
              href="https://community.home-assistant.io/t/smart-irrigation-save-water-by-precisely-watering-your-lawn-garden"
              >${localize(
                "panels.help.cards.how-to-get-help.community-forum",
                this.hass.language,
              )}</a
            >
            ${localize(
              "panels.help.cards.how-to-get-help.or-open-a",
              this.hass.language,
            )}
            <a
              href="https://github.com/jeroenterheerdt/HAsmartirrigation/issues"
              >${localize(
                "panels.help.cards.how-to-get-help.github-issue",
                this.hass.language,
              )}</a
            >
            (${localize(
              "panels.help.cards.how-to-get-help.english-only",
              this.hass.language,
            )}).
          </div></ha-card
        >`;
      default:
        return html`
          <ha-card header="Page not found">
            <div class="card-content">
              The page you are trying to reach cannot be found. Please select a
              page from the menu above to continue.
            </div>
          </ha-card>
        `;
    }
  }

  handlePageSelected(ev: CustomEvent) {
    // Try multiple ways to get the page name
    const newPage =
      ev.detail.name ||
      ev.detail.panel ||
      (ev.target as any)?.getAttribute?.("panel") ||
      ev.detail.item?.getAttribute?.("panel");

    if (newPage && newPage !== getPath().page) {
      navigate(this, exportPath(newPage));
      // Don't call requestUpdate here - the location-changed event will handle it
    } else {
      scrollTo(0, 0);
    }
  }

  static get styles(): CSSResultGroup {
    return css`
      ${commonStyle} :host {
        color: var(--primary-text-color);
        --paper-card-header-color: var(--primary-text-color);
      }
      .header {
        background-color: var(--app-header-background-color);
        color: var(--app-header-text-color, white);
        border-bottom: var(--app-header-border-bottom, none);
      }
      .toolbar {
        height: var(--header-height);
        display: flex;
        align-items: center;
        font-size: 20px;
        padding: 0 16px;
        font-weight: 400;
        box-sizing: border-box;
      }
      .main-title {
        margin: 0 0 0 24px;
        line-height: 20px;
        flex-grow: 1;
      }
      sl-tab-group {
        margin-left: max(env(safe-area-inset-left), 24px);
        margin-right: max(env(safe-area-inset-right), 24px);
        --ha-tab-active-text-color: var(--app-header-text-color, white);
        --ha-tab-indicator-color: var(--app-header-text-color, white);
        --ha-tab-track-color: transparent;
        text-transform: uppercase;
      }

      .view {
        height: calc(100vh - 112px);
        display: flex;
        justify-content: center;
      }

      .view > * {
        width: 600px;
        max-width: 600px;
      }

      .view > *:last-child {
        margin-bottom: 20px;
      }

      .version {
        font-size: 14px;
        font-weight: 500;
        color: rgba(var(--rgb-text-primary-color), 0.9);
      }
    `;
  }
}
