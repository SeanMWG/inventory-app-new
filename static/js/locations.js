// Location Management Module
const locations = {
    currentFilters: {
        search: '',
        room_type: '',
        site: '',
        status: 'active'
    },
    
    init: function() {
        this.bindEvents();
        this.loadFilters();
        this.loadLocations();
    },
    
    bindEvents: function() {
        // Search
        $('#searchInput').on('keyup', _.debounce(() => {
            this.currentFilters.search = $('#searchInput').val();
            this.loadLocations();
        }, 300));
        
        // Filters
        $('.filter-select').on('change', () => {
            this.currentFilters.room_type = $('#roomTypeFilter').val();
            this.currentFilters.site = $('#siteFilter').val();
            this.currentFilters.status = $('#statusFilter').val();
            this.loadLocations();
        });
        
        // Add/Edit Location
        $('#addLocationBtn').on('click', () => this.showLocationModal());
        $('#saveLocationBtn').on('click', () => this.saveLocation());
        
        // View Location Details
        $(document).on('click', '.view-location', (e) => {
            const locationId = $(e.currentTarget).data('location-id');
            this.showLocationDetails(locationId);
        });
        
        // Edit Location
        $(document).on('click', '.edit-location, #editLocationBtn', (e) => {
            const locationId = $(e.currentTarget).data('location-id');
            this.showLocationModal(locationId);
        });
        
        // Delete Location
        $(document).on('click', '.delete-location', (e) => {
            const locationId = $(e.currentTarget).data('location-id');
            if (confirm('Are you sure you want to delete this location?')) {
                this.deleteLocation(locationId);
            }
        });
    },
    
    loadFilters: async function() {
        try {
            // Load room types
            const roomTypes = await $.get(`${API.locations}/types`);
            const roomTypeSelect = $('#roomTypeFilter');
            roomTypes.forEach(type => {
                roomTypeSelect.append(`<option value="${type}">${type}</option>`);
            });
            
            // Load sites
            const response = await $.get(API.locations);
            const sites = [...new Set(response.map(loc => loc.site_name))].sort();
            const siteSelect = $('#siteFilter');
            sites.forEach(site => {
                siteSelect.append(`<option value="${site}">${site}</option>`);
            });
        } catch (error) {
            utils.showError('Failed to load filters');
            console.error('Error loading filters:', error);
        }
    },
    
    loadLocations: async function() {
        const container = $('#locationsGrid');
        utils.showLoading(container);
        
        try {
            const queryString = $.param(this.currentFilters);
            const locations = await $.get(`${API.locations}?${queryString}`);
            
            container.empty();
            locations.forEach(location => {
                container.append(locationCardTemplate(location));
            });
        } catch (error) {
            utils.showError('Failed to load locations');
            console.error('Error loading locations:', error);
        } finally {
            utils.hideLoading(container);
        }
    },
    
    showLocationModal: function(locationId = null) {
        const modal = $('#locationModal');
        modal.find('form')[0].reset();
        
        if (locationId) {
            // Edit mode
            $('#modalTitle').text('Edit Location');
            $.get(`${API.locations}/${locationId}`)
                .then(location => {
                    $('#siteName').val(location.site_name);
                    $('#roomNumber').val(location.room_number);
                    $('#roomName').val(location.room_name);
                    $('#roomType').val(location.room_type);
                    $('#floor').val(location.floor);
                    $('#building').val(location.building);
                    $('#description').val(location.description);
                    modal.data('location-id', locationId);
                })
                .catch(error => {
                    utils.showError('Failed to load location details');
                    console.error('Error loading location:', error);
                });
        } else {
            // Add mode
            $('#modalTitle').text('Add Location');
            modal.removeData('location-id');
        }
        
        modal.modal('show');
    },
    
    saveLocation: async function() {
        const modal = $('#locationModal');
        const locationId = modal.data('location-id');
        
        const data = {
            site_name: $('#siteName').val(),
            room_number: $('#roomNumber').val(),
            room_name: $('#roomName').val(),
            room_type: $('#roomType').val(),
            floor: $('#floor').val(),
            building: $('#building').val(),
            description: $('#description').val()
        };
        
        try {
            if (locationId) {
                // Update existing location
                await $.ajax({
                    url: `${API.locations}/${locationId}`,
                    method: 'PUT',
                    data: JSON.stringify(data),
                    contentType: 'application/json'
                });
                utils.showSuccess('Location updated successfully');
            } else {
                // Create new location
                await $.ajax({
                    url: API.locations,
                    method: 'POST',
                    data: JSON.stringify(data),
                    contentType: 'application/json'
                });
                utils.showSuccess('Location created successfully');
            }
            
            modal.modal('hide');
            this.loadLocations();
        } catch (error) {
            utils.showError('Failed to save location');
            console.error('Error saving location:', error);
        }
    },
    
    showLocationDetails: async function(locationId) {
        const modal = $('#locationDetailsModal');
        
        try {
            const [location, history] = await Promise.all([
                $.get(`${API.locations}/${locationId}`),
                $.get(`${API.locations}/${locationId}/history`)
            ]);
            
            // Fill in location details
            $('#detailsSiteName').text(location.site_name);
            $('#detailsRoomNumber').text(location.room_number);
            $('#detailsRoomName').text(location.room_name);
            $('#detailsRoomType').text(location.room_type);
            $('#detailsFloor').text(location.floor || '-');
            $('#detailsBuilding').text(location.building || '-');
            $('#detailsDescription').text(location.description || 'No description available');
            
            // Fill in statistics
            $('#detailsItemCount').text(location.inventory_items?.length || 0);
            $('#detailsActiveCount').text(
                location.inventory_items?.filter(item => item.status === 'active').length || 0
            );
            $('#detailsLoanerCount').text(
                location.inventory_items?.filter(item => item.is_loaner).length || 0
            );
            
            // Fill in activity history
            const activityBody = $('#detailsActivity');
            activityBody.empty();
            
            history.forEach(entry => {
                activityBody.append(`
                    <tr>
                        <td>${utils.formatDate(entry.changed_at)}</td>
                        <td>${entry.action_type} ${entry.field_name}</td>
                        <td>${entry.changed_by}</td>
                    </tr>
                `);
            });
            
            // Store location ID for edit button
            modal.data('location-id', locationId);
            
            modal.modal('show');
        } catch (error) {
            utils.showError('Failed to load location details');
            console.error('Error loading location details:', error);
        }
    },
    
    deleteLocation: async function(locationId) {
        try {
            await $.ajax({
                url: `${API.locations}/${locationId}`,
                method: 'DELETE'
            });
            utils.showSuccess('Location deleted successfully');
            this.loadLocations();
        } catch (error) {
            utils.showError('Failed to delete location');
            console.error('Error deleting location:', error);
        }
    }
};

// Initialize when document is ready
$(document).ready(function() {
    // Initialize location management if on locations page
    if ($('#locationsGrid').length) {
        locations.init();
    }
});
