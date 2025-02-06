// API Endpoints
const API = {
    inventory: '/api/inventory',
    locations: '/api/locations',
    auth: '/auth'
};

// Utility Functions
const utils = {
    formatDate: function(dateString) {
        if (!dateString) return '';
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },
    
    showLoading: function(element) {
        element.addClass('loading');
    },
    
    hideLoading: function(element) {
        element.removeClass('loading');
    },
    
    showError: function(message) {
        const alert = $(`
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `);
        $('.container').first().prepend(alert);
    },
    
    showSuccess: function(message) {
        const alert = $(`
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `);
        $('.container').first().prepend(alert);
    }
};

// Inventory Management
const inventory = {
    currentFilters: {
        page: 1,
        per_page: 25,
        search: '',
        asset_type: '',
        room_type: '',
        status: 'active'
    },
    
    init: function() {
        this.bindEvents();
        this.loadFilters();
        this.loadInventory();
    },
    
    bindEvents: function() {
        // Search
        $('#searchInput').on('keyup', _.debounce(() => {
            this.currentFilters.search = $('#searchInput').val();
            this.currentFilters.page = 1;
            this.loadInventory();
        }, 300));
        
        // Filters
        $('.filter-select').on('change', () => {
            this.currentFilters.asset_type = $('#assetTypeFilter').val();
            this.currentFilters.room_type = $('#roomTypeFilter').val();
            this.currentFilters.status = $('#statusFilter').val();
            this.currentFilters.page = 1;
            this.loadInventory();
        });
        
        // Pagination
        $(document).on('click', '.page-link', (e) => {
            e.preventDefault();
            const page = $(e.currentTarget).data('page');
            if (page) {
                this.currentFilters.page = page;
                this.loadInventory();
            }
        });
        
        // Add/Edit Item Modal
        $('#addItemBtn').on('click', () => this.showItemModal());
        $('#itemModal').on('show.bs.modal', () => this.loadLocations());
        $('#saveItemBtn').on('click', () => this.saveItem());
        
        // Delete Item
        $(document).on('click', '.delete-item', (e) => {
            const assetTag = $(e.currentTarget).data('asset-tag');
            if (confirm('Are you sure you want to delete this item?')) {
                this.deleteItem(assetTag);
            }
        });
        
        // Toggle Loaner Status
        $(document).on('click', '.toggle-loaner', (e) => {
            const assetTag = $(e.currentTarget).data('asset-tag');
            this.toggleLoanerStatus(assetTag);
        });
    },
    
    loadFilters: async function() {
        try {
            // Load asset types
            const assetTypes = await $.get(`${API.inventory}/types`);
            const assetTypeSelect = $('#assetTypeFilter');
            assetTypes.forEach(type => {
                assetTypeSelect.append(`<option value="${type}">${type}</option>`);
            });
            
            // Load room types
            const roomTypes = await $.get(`${API.locations}/types`);
            const roomTypeSelect = $('#roomTypeFilter');
            roomTypes.forEach(type => {
                roomTypeSelect.append(`<option value="${type}">${type}</option>`);
            });
        } catch (error) {
            utils.showError('Failed to load filters');
            console.error('Error loading filters:', error);
        }
    },
    
    loadInventory: async function() {
        const container = $('#inventoryTable');
        utils.showLoading(container);
        
        try {
            const queryString = $.param(this.currentFilters);
            const response = await $.get(`${API.inventory}?${queryString}`);
            
            this.renderInventoryTable(response);
            this.renderPagination(response);
        } catch (error) {
            utils.showError('Failed to load inventory');
            console.error('Error loading inventory:', error);
        } finally {
            utils.hideLoading(container);
        }
    },
    
    renderInventoryTable: function(data) {
        const tbody = $('#inventoryTable tbody');
        tbody.empty();
        
        data.items.forEach(item => {
            tbody.append(`
                <tr>
                    <td>${item.asset_tag}</td>
                    <td>${item.asset_type}</td>
                    <td>${item.manufacturer || ''} ${item.model || ''}</td>
                    <td>${item.location?.full_name || ''}</td>
                    <td>${item.assigned_to || ''}</td>
                    <td>
                        <span class="badge badge-${item.status}">${item.status}</span>
                        ${item.is_loaner ? '<span class="badge badge-loaner">Loaner</span>' : ''}
                    </td>
                    <td>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary edit-item" 
                                    data-asset-tag="${item.asset_tag}">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-info toggle-loaner" 
                                    data-asset-tag="${item.asset_tag}">
                                <i class="fas fa-handshake"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger delete-item" 
                                    data-asset-tag="${item.asset_tag}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `);
        });
    },
    
    renderPagination: function(data) {
        const pagination = $('.pagination');
        pagination.empty();
        
        // Previous button
        pagination.append(`
            <li class="page-item ${data.current_page === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${data.current_page - 1}">Previous</a>
            </li>
        `);
        
        // Page numbers
        for (let i = 1; i <= data.pages; i++) {
            pagination.append(`
                <li class="page-item ${i === data.current_page ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `);
        }
        
        // Next button
        pagination.append(`
            <li class="page-item ${data.current_page === data.pages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${data.current_page + 1}">Next</a>
            </li>
        `);
    },
    
    loadLocations: async function() {
        try {
            const locations = await $.get(API.locations);
            const select = $('#locationSelect');
            select.empty();
            select.append('<option value="">No Location</option>');
            
            locations.forEach(location => {
                select.append(`
                    <option value="${location.id}">${location.full_name}</option>
                `);
            });
        } catch (error) {
            utils.showError('Failed to load locations');
            console.error('Error loading locations:', error);
        }
    },
    
    showItemModal: function(assetTag = null) {
        const modal = $('#itemModal');
        modal.find('form')[0].reset();
        
        if (assetTag) {
            // Edit mode
            $.get(`${API.inventory}/${assetTag}`)
                .then(item => {
                    $('#assetTag').val(item.asset_tag);
                    $('#assetType').val(item.asset_type);
                    $('#manufacturer').val(item.manufacturer);
                    $('#model').val(item.model);
                    $('#serialNumber').val(item.serial_number);
                    $('#locationSelect').val(item.location_id);
                    $('#assignedTo').val(item.assigned_to);
                    $('#notes').val(item.notes);
                    $('#isLoaner').prop('checked', item.is_loaner);
                })
                .catch(error => {
                    utils.showError('Failed to load item details');
                    console.error('Error loading item:', error);
                });
        }
        
        modal.modal('show');
    },
    
    saveItem: async function() {
        const form = $('#itemModal form');
        const data = {
            asset_tag: $('#assetTag').val(),
            asset_type: $('#assetType').val(),
            manufacturer: $('#manufacturer').val(),
            model: $('#model').val(),
            serial_number: $('#serialNumber').val(),
            location_id: $('#locationSelect').val() || null,
            assigned_to: $('#assignedTo').val(),
            notes: $('#notes').val(),
            is_loaner: $('#isLoaner').is(':checked')
        };
        
        try {
            if ($('#assetTag').prop('readonly')) {
                // Update existing item
                await $.ajax({
                    url: `${API.inventory}/${data.asset_tag}`,
                    method: 'PUT',
                    data: JSON.stringify(data),
                    contentType: 'application/json'
                });
                utils.showSuccess('Item updated successfully');
            } else {
                // Create new item
                await $.ajax({
                    url: API.inventory,
                    method: 'POST',
                    data: JSON.stringify(data),
                    contentType: 'application/json'
                });
                utils.showSuccess('Item created successfully');
            }
            
            $('#itemModal').modal('hide');
            this.loadInventory();
        } catch (error) {
            utils.showError('Failed to save item');
            console.error('Error saving item:', error);
        }
    },
    
    deleteItem: async function(assetTag) {
        try {
            await $.ajax({
                url: `${API.inventory}/${assetTag}`,
                method: 'DELETE'
            });
            utils.showSuccess('Item deleted successfully');
            this.loadInventory();
        } catch (error) {
            utils.showError('Failed to delete item');
            console.error('Error deleting item:', error);
        }
    },
    
    toggleLoanerStatus: async function(assetTag) {
        try {
            const response = await $.post(`${API.inventory}/${assetTag}/toggle-loaner`);
            utils.showSuccess(`Loaner status ${response.is_loaner ? 'enabled' : 'disabled'}`);
            this.loadInventory();
        } catch (error) {
            utils.showError('Failed to toggle loaner status');
            console.error('Error toggling loaner status:', error);
        }
    }
};

// Initialize when document is ready
$(document).ready(function() {
    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Initialize inventory management if on inventory page
    if ($('#inventoryTable').length) {
        inventory.init();
    }
    
    // Handle session timeout
    $(document).ajaxError(function(event, jqXHR) {
        if (jqXHR.status === 401) {
            window.location.href = `${API.auth}/login`;
        }
    });
});
