// api.js
export const ConfigAPI = {
    /**
     * Fetch all configurations
     */
    async getAll() {
        // Keep the cache buster from your original code
        const cacheBuster = `?t=${Date.now()}`;
        const response = await fetch(`/api/configs${cacheBuster}`);
        
        if (!response.ok) {
            throw new Error(`Failed to load configs: ${response.statusText}`);
        }
        return response.json();
    },

    /**
     * Create a duplicate of a configuration
     */
    async duplicate(baseId, newName, category) {
        const response = await fetch(`/api/config/create`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: newName,
                target: category.toLowerCase(),
                base_id: baseId
            })
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.message || "Failed to duplicate configuration");
        }
        return response.json();
    },

    /**
     * Delete a configuration
     */
    async delete(configId) {
        const response = await fetch(`/api/config/${configId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${response.status}`);
        }
        return true;
    },

    /**
     * Save a configuration (used for removing ghost rules, etc)
     */
    async save(config) {
        const response = await fetch(`/api/config/${config.id}/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config: { rules: config.rules } })
        });

        if (!response.ok) {
            throw new Error('Failed to save configuration');
        }
        return response.json();
    }
};