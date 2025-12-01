# Configuration Module

This directory contains the logic for managing Rule Configurations in Arcane Auditor. It adheres to a **Controller-View-Service** architecture to separate business logic from UI rendering and API calls.

## 📂 File Structure

### 1. `manager.js` ( The Controller)

* **Role:** The brain of the operation.
* **Responsibilities:**
  * Initializes the UI components.
  * Holds the state (current selected config, available configs).
  * Orchestrates data flow between the API and the UI.
  * Handles high-level actions (e.g., `requestDeleteConfiguration`, `saveCurrentConfigChanges`).

### 2. `api.js` (The Service)

* **Role:** The raw data layer.
* **Responsibilities:**
  * Handles all `fetch` calls to the backend.
  * Manages HTTP headers and JSON serialization.
  * Standardizes error throwing for the Controller to catch.
  * *No UI logic allowed here.*

### 3. `ui-main.js` (The Dashboard View)

* **Role:** Manages the persistent UI elements on the main page.
* **Responsibilities:**
  * Updates the **Toolbar** (Selected config name, category badge).
  * Builds and toggles the **Dropdown** menu.
  * Updates the metadata summary line.

### 4. `ui-breakdown.js` (The Editor View)

* **Role:** Manages the "Manage Rules" modal.
* **Responsibilities:**
  * Renders the list of rules with toggle switches.
  * Handles "Severity" dropdowns and "JSON Settings" inputs.
  * Manages the local state of the config object while editing (in-memory mutation).
  * Handles Save, Duplicate, and Delete actions inside the modal header.

---

## 🔄 Key Workflows

### Loading Configurations

`manager.loadConfigurations()` → `api.getAll()` → `ui.refreshAll()`

### Saving Rules

1. User toggles a switch in **Breakdown Modal** (`ui-breakdown.js`).
2. The in-memory `config` object is updated immediately by reference.
3. User clicks **Save**.
4. `manager.saveCurrentConfigChanges()` is called.
5. Manager strips the object down to `{ id, rules }`.
6. `api.save()` sends payload to backend.
7. Manager reloads all configs to sync state.

## 🛠 Usage

Initialized in `app.js`:

```javascript
import { ConfigManager } from './config/manager.js';

const app = new App();
this.configManager = new ConfigManager(this);
```
