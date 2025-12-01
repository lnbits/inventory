window.app = Vue.createApp({
  el: '#vue',
  mixins: [windowMixin],
  // Declare models/variables
  data() {
    return {
      tab: 'items',
      tabOptions: [
        {label: 'Items', value: 'items'},
        // {label: 'Stock Managers', value: 'managers'},
        {label: 'Services', value: 'services'},
        {label: 'Stock Logs', value: 'orders'},
        {label: 'Settings', value: 'settings'}
      ],
      currencyOptions: [],
      inventory: null,
      managers: [],
      services: [],
      items: [],
      logs: [],
      inventoryDialog: {
        show: false,
        data: {}
      },
      managerDialog: {
        show: false,
        data: {}
      },
      serviceDialog: {
        show: false,
        data: {}
      },
      openInventory: null,
      openInventoryCurrency: null,
      itemGrid: true,
      itemDialog: {
        show: false,
        data: {},
        gallery: [],
        currency: null
      },
      itemsTable: {
        columns: [
          {
            name: 'is_active',
            align: 'left',
            label: '',
            field: 'is_active',
            sortable: false,
            format: (_, row) => (row.is_active === true ? '🟢' : '⚪')
          },
          {
            name: 'name',
            align: 'left',
            label: 'Name',
            field: 'name',
            sortable: true
          },
          {
            name: 'description',
            align: 'left',
            label: 'Description',
            field: 'description',
            sortable: false,
            format: val => (val || '').substring(0, 50)
          },
          {
            name: 'price',
            align: 'left',
            label: 'Price',
            field: 'price',
            sortable: true,
            format: (_, row) =>
              this.checkIsSat(this.openInventoryCurrency)
                ? `${row.price} sats`
                : LNbits.utils.formatCurrency(row.price, this.openInventoryCurrency)
          },
          {
            name: 'discount',
            align: 'left',
            label: 'Discount',
            field: 'discount_percentage',
            sortable: true,
            format: val => (val ? `${val}%` : '')
          },
          {
            name: 'quantity_in_stock',
            align: 'center',
            label: 'Quantity',
            field: 'quantity_in_stock',
            sortable: true
          },
          {
            name: 'low_stock',
            align: 'center',
            label: 'Low Stock',
            field: 'reorder_threshold',
            sortable: true,
            format: (val, row) => {
              if (val === null || val === undefined) return ''
              return row.quantity_in_stock && val >= row.quantity_in_stock
                ? '⚠️'
                : ''
            }
          },
          {
            name: 'tags',
            align: 'left',
            label: 'Tags',
            field: 'tags',
            sortable: true,
            format: val => (val ? val.toString() : '')
          },
          {
            name: 'categories',
            align: 'left',
            label: 'Categories',
            field: 'categories',
            sortable: true,
            format: val => (val ? val.toString() : '')
          },
          {
            name: 'created_at',
            align: 'left',
            label: 'Created At',
            field: 'created_at',
            format: val => LNbits.utils.formatDateString(val),
            sortable: true
          },
          {
            name: 'id',
            align: 'left',
            label: 'ID',
            field: 'id',
            sortable: true
          }
        ],
        pagination: {
          rowsPerPage: 10,
          page: 1,
          rowsNumber: 10
        },
        search: '',
        filter: {
          is_approved: true
        }
      },
      loadingItems: false,
      categories: [],
      servicesTable: {
        columns: [
          {
            name: 'name',
            align: 'left',
            label: 'Name',
            field: 'service_name',
            sortable: true
          },
          {
            name: 'description',
            align: 'left',
            label: 'Description',
            field: 'description',
            sortable: false,
            format: val => (val || '').substring(0, 50)
          },
          {
            name: 'api_key',
            align: 'left',
            label: 'API Key',
            field: 'api_key',
            sortable: true,
            format: val =>
              val
                ? val.substring(0, 8) + '...' + val.substring(val.length - 8)
                : ''
          },
          {
            name: 'tags',
            align: 'left',
            label: 'Tags',
            field: 'tags',
            sortable: true,
            format: val => (val ? val.toString() : '')
          },
          {
            name: 'active',
            align: 'left',
            label: 'Active',
            field: 'is_active',
            sortable: true,
            format: val => (val ? 'Yes' : 'No')
          },
          {
            name: 'created_at',
            align: 'left',
            label: 'Created At',
            field: 'created_at',
            format: val => LNbits.utils.formatDateString(val),
            sortable: true
          },
          {
            name: 'last_used_at',
            align: 'left',
            label: 'Last Used At',
            field: 'last_used_at',
            format: val => (val ? LNbits.utils.formatDateString(val) : 'Never'),
            sortable: true
          }
        ],
        pagination: {
          rowsPerPage: 10,
          page: 1,
          rowsNumber: 10
        },
        search: '',
        filter: {}
      },
      stockLogsTable: {
        columns: [
          {
            name: 'source',
            align: 'left',
            label: 'Source',
            field: 'source',
            sortable: true
          },
          {
            name: 'quantity_change',
            align: 'left',
            label: 'Quantity Change',
            field: 'quantity_change',
            sortable: true
          },
          {
            name: 'quantity_after',
            align: 'left',
            label: 'Quantity After',
            field: 'quantity_after',
            sortable: true
          },
          {
            name: 'item_id',
            align: 'left',
            label: 'Item ID',
            field: 'item_id',
            sortable: true
          },
          {
            name: 'external_service_id',
            align: 'left',
            label: 'External Service ID',
            field: 'external_service_id',
            sortable: true
          },
          {
            name: 'created_at',
            align: 'left',
            label: 'Created At',
            field: 'created_at',
            format: val => LNbits.utils.formatDateString(val),
            sortable: true
          }
        ],
        pagination: {
          rowsPerPage: 10,
          page: 1,
          rowsNumber: 10
        },
        search: '',
        filter: {}
      }
    }
  },
  computed: {
    isSatCurrency() {
      return this.checkIsSat(this.itemDialog.currency)
    },
    allowCurrencyDecimals() {
      return (this.getCurrencyDecimals(this.itemDialog.currency) || 0) > 0
    }
  },
  watch: {
    'itemsTable.search': {
      handler() {
        this.getItemsPaginated()
      }
    },
    async tab(newTab) {
      if (newTab === 'items') {
        this.itemsTable.pagination = {
          rowsPerPage: 10,
          page: 1,
          rowsNumber: 10
        }
        this.itemsTable.search = ''
        this.itemsTable.filter = {is_approved: true}
        await this.getItemsPaginated()
      } else if (newTab === 'services') {
        await this.getServices()
      } else if (newTab === 'orders') {
        await this.getStockLogsPaginated()
      }
    }
  },
  methods: {
    showInventoryDialog() {
      this.inventoryDialog.show = true
      if (this.inventory) {
        const tags =
          typeof this.inventory.tags === 'string'
            ? fromCsv(this.inventory.tags)
            : this.inventory.tags || []
        this.inventoryDialog.data = {...this.inventory, tags}
        return
      }
      this.inventoryDialog.data = {}
      this.inventoryDialog.data.is_tax_inclusive = true
      this.inventoryDialog.data.currency = this.defaultCurrency()
    },
    closeInventoryDialog() {
      this.inventoryDialog.show = false
      this.inventoryDialog.data = {}
    },
    closeManagerDialog() {
      this.managerDialog.show = false
      this.managerDialog.data = {}
    },
    closeServiceDialog() {
      this.serviceDialog.show = false
      this.serviceDialog.data = {}
    },
    createOrUpdateDisabled() {
      if (!this.inventoryDialog.show) return true
      const data = this.inventoryDialog.data
      return !data.name || !data.currency
    },
    normalizeCurrency(currency) {
      if (!currency) return null
      return this.checkIsSat(currency) ? 'sat' : currency.toUpperCase()
    },
    defaultCurrency() {
      const userCurrency =
        this.g?.wallet?.currency || this.g?.user?.wallets?.[0]?.currency
      return this.normalizeCurrency(userCurrency) || 'sat'
    },
    setInventoryCurrencies(currency) {
      const normalized = this.normalizeCurrency(currency) || this.defaultCurrency()
      this.openInventoryCurrency = normalized
      this.itemDialog.currency = normalized
    },
    checkIsSat(currency) {
      return ['sat', 'sats'].includes((currency || '').toLowerCase())
    },
    getCurrencyDecimals(currency) {
      const normalized = this.normalizeCurrency(currency) || this.defaultCurrency()
      if (this.checkIsSat(normalized)) return 0
      try {
        const resolved = new Intl.NumberFormat(window.i18n.global.locale, {
          style: 'currency',
          currency: normalized
        }).resolvedOptions()
        return resolved.maximumFractionDigits || 0
      } catch (error) {
        return 2
      }
    },
    async getInventories() {
      try {
        const {data} = await LNbits.api.request(
          'GET',
          '/inventory/api/v1'
        )
        if (!data || (Array.isArray(data) && data.length === 0)) {
          this.inventory = null
          this.openInventory = null
          this.setInventoryCurrencies(null)
          this.items = []
          return
        }
        const inventoryData = Array.isArray(data) ? data[0] : data
        inventoryData.tags = fromCsv(inventoryData.tags)
        this.inventory = {...inventoryData} // Change to single inventory
        this.openInventory = this.inventory.id
        this.setInventoryCurrencies(this.inventory.currency)
        await this.getItemsPaginated()
        await this.getCategories()
        await this.getManagers()
        console.log('Fetched inventory:', this.inventory)
      } catch (error) {
        console.error('Error fetching inventory:', error)
      }
    },
    submitInventoryData() {
      const data = this.inventoryDialog.data
      if (data.tags && Array.isArray(data.tags)) {
        data.tags = data.tags.join(',')
      }
      if (data.id) {
        this.updateInventory(data)
      } else {
        this.createInventory(data)
      }
    },
    async createInventory(data) {
      try {
        const payload = {...data}
        const {data: createdInventory} = await LNbits.api.request(
          'POST',
          '/inventory/api/v1',
          null,
          payload
        )
        createdInventory.tags = fromCsv(createdInventory.tags)
        this.inventory = {...createdInventory}
        this.openInventory = this.inventory.id
        this.setInventoryCurrencies(this.inventory.currency)
        this.tab = 'items'
        await this.getItemsPaginated()
      } catch (error) {
        console.error('Error creating inventory:', error)
        LNbits.utils.notifyError(error)
      } finally {
        this.closeInventoryDialog()
      }
    },
    async updateInventory(data) {
      try {
        const {data: updatedInventory} = await LNbits.api.request(
          'PUT',
          `/inventory/api/v1/${data.id}`,
          null,
          data
        )
        updatedInventory.tags = fromCsv(updatedInventory.tags)
        this.inventory = {...updatedInventory}
      } catch (error) {
        console.error('Error updating inventory:', error)
        LNbits.utils.notifyError(error)
      } finally {
        this.closeInventoryDialog()
      }
    },
    async deleteInventory(id) {
      this.$q
        .dialog({
          title: 'Confirm Deletion',
          message: 'Are you sure you want to delete this inventory?',
          cancel: true,
          persistent: true
        })
        .onOk(async () => {
          try {
            await LNbits.api.request(
              'DELETE',
              `/inventory/api/v1/${id}`
            )
            this.inventory = null
            this.openInventory = null
            this.items = []
            this.categories = []
            this.managers = []
            this.services = []
            this.logs = []
            this.closeInventoryDialog()
            this.$q.notify({
              type: 'positive',
              message: 'Inventory deleted successfully.'
            })
          } catch (error) {
            console.error('Error deleting inventory:', error)
            LNbits.utils.notifyError(error)
          }
        })
    },
    toggleItemView() {
      this.itemGrid = !this.itemGrid
      this.$q.localStorage.set('lnbits_inventoryItemGrid', this.itemGrid)
    },
    itemsTabPagination(page) {
      this.itemsTable.pagination.page = page
      this.getItemsPaginated()
    },
    async getItemsPaginated(props) {
      if (!this.openInventory) {
        this.items = []
        this.itemsTable.pagination.rowsNumber = 0
        return
      }
      console.log('Getting paginated items with props:', props)
      this.loadingItems = true
      try {
        const params = LNbits.utils.prepareFilterQuery(this.itemsTable, props)
        console.log('Constructed query params:', params)
        const {data} = await LNbits.api.request(
          'GET',
          `/inventory/api/v1/items/${this.openInventory}/paginated?${params}`
        )
        console.log('Fetched paginated items:', data)
        this.items = data.data.map(item => mapItems(item))
        this.itemsTable.pagination.rowsNumber = data.total
      } catch (error) {
        console.error('Error fetching items:', error)
        LNbits.utils.notifyError(error)
      } finally {
        this.loadingItems = false
      }
    },
    async getCategories() {
      try {
        const {data} = await LNbits.api.request(
          'GET',
          `/inventory/api/v1/categories/${this.openInventory}`
        )
        console.log('Fetched categories:', data)
        this.categories = [...data]
      } catch (error) {
        console.error('Error fetching categories:', error)
        LNbits.utils.notifyError(error)
      }
    },
    createNewCategory(val, done) {
      if (val.length === 0) return
    },
    showItemDialog(id) {
      if (!this.inventory) return
      this.itemDialog.show = true
      this.setInventoryCurrencies(this.inventory?.currency)
      if (id) {
        const item = this.items.find(it => it.id === id)
        console.log('Editing item:', item)
        this.itemDialog.data = {...item}
        this.itemDialog.gallery = item.images.map(id => {
          return {
            assetId: id,
            preview: isBase64String(id) ? id : `/api/v1/assets/${id}/thumbnail`,
            file: null,
            isNew: false
          }
        })
        return
      }
      this.itemDialog.data = {}
    },
    closeItemDialog() {
      this.itemDialog.show = false
      this.itemDialog.data = {}
      this.itemDialog.gallery.forEach(p => {
        // cleanup object URLs
        if (p.preview && p.isNew) URL.revokeObjectURL(p.preview)
      })
      this.itemDialog.gallery = []
    },
    submitItemData() {
      const data = this.itemDialog.data
      data.tags = toCsv(data.tags)
      console.log('Submitting inventory data:', data)
      console.log('photos:', this.itemDialog.gallery)
      if (data.id) {
        this.updateItem(data)
      } else {
        this.addItem()
      }
    },
    async uploadPhoto(photoFile) {
      const form = new FormData()
      form.append('file', photoFile)
      form.append('public_asset', 'true')

      try {
        const {data} = await LNbits.api.request(
          'POST',
          '/api/v1/assets?public_asset=true',
          null,
          form
        )
        return data.id
      } catch (error) {
        console.error('Photo upload error:', error)
        return null
      }
    },
    async addItem() {
      this.itemDialog.data.inventory_id = this.inventory.id
      try {
        const assetIds = await Promise.all(
          this.itemDialog.gallery
            .filter(p => p.file)
            .map(p => this.uploadPhoto(p.file))
        )
        if (assetIds.includes(null)) {
          LNbits.utils.notifyError('One or more photo uploads failed')
          return
        }
        this.itemDialog.data.images = toCsv(assetIds)
        const {data} = await LNbits.api.request(
          'POST',
          `/inventory/api/v1/items`,
          null,
          this.itemDialog.data
        )
        console.log('Item added:', data)
        this.items = [...this.items, mapItems(data)]
        this.itemDialog.show = false
        this.itemDialog.data = {}
      } catch (error) {
        console.error('Error adding item:', error)
        LNbits.utils.notifyError(error)
      }
    },
    async updateItem(data) {
      const newPhotos = this.itemDialog.gallery.filter(p => p.isNew && p.file)
      let newAssetIds = []

      if (newPhotos.length > 0) {
        try {
          newAssetIds = await Promise.all(
            newPhotos.map(p => this.uploadPhoto(p.file))
          )
        } catch (error) {
          LNbits.utils.notifyError('Failed to upload new photos')
          return
        }
      }

      const finalIds = [
        ...this.itemDialog.gallery
          .filter(p => !p.isNew && p.assetId)
          .map(p => p.assetId),
        ...newAssetIds
      ]

      data.images = toCsv(finalIds)

      try {
        const {data: updatedItem} = await LNbits.api.request(
          'PUT',
          `/inventory/api/v1/items/${data.id}`,
          null,
          data
        )
        this.items = this.items.map(item =>
          item.id === updatedItem.id ? mapItems(updatedItem) : item
        )
      } catch (error) {
        console.error('Error updating item:', error)
        LNbits.utils.notifyError(error)
      } finally {
        this.closeItemDialog()
      }
    },
    async deleteItem(id) {
      this.$q
        .dialog({
          title: 'Confirm Deletion',
          message: 'Are you sure you want to delete this item?',
          cancel: true,
          persistent: true
        })
        .onOk(async () => {
          try {
            await LNbits.api.request('DELETE', `/inventory/api/v1/items/${id}`)
            this.items = this.items.filter(item => item.id !== id)
          } catch (error) {
            console.error('Error deleting item:', error)
            LNbits.utils.notifyError(error)
          }
        })
    },
    async getManagers() {
      try {
        const {data} = await LNbits.api.request(
          'GET',
          `/inventory/api/v1/managers/${this.openInventory}`
        )
        this.managers = [...data]
      } catch (error) {
        console.error('Error fetching managers:', error)
        LNbits.utils.notifyError(error)
      }
    },
    showManagerDialog(id) {
      this.managerDialog.show = true
      if (id) {
        const manager = this.managers.find(mgr => mgr.id === id)
        this.managerDialog.data = {...manager}
        return
      }
      this.managerDialog.data = {}
    },
    submitManagerData() {
      const inventoryId = this.openInventory
      if (!inventoryId) {
        LNbits.utils.notifyError('No inventory selected')
        return
      }
      this.managerDialog.data.inventory_id = inventoryId
      if (this.managerDialog.data.id) {
        this.updateManager(this.managerDialog.data)
      } else {
        this.createManager(this.managerDialog.data)
      }
    },
    async createManager(data) {
      try {
        const payload = {...data}
        const {data: createdManager} = await LNbits.api.request(
          'POST',
          `/inventory/api/v1/managers/${this.openInventory}`,
          null,
          payload
        )
        this.managers = [...this.managers, createdManager]
      } catch (error) {
        console.error('Error creating manager:', error)
        LNbits.utils.notifyError(error)
      } finally {
        this.closeManagerDialog()
      }
    },
    async updateManager(data) {
      try {
        const {data: updatedManager} = await LNbits.api.request(
          'PUT',
          `/inventory/api/v1/managers/${data.id}`,
          null,
          payload
        )
        this.managers = this.managers.map(manager =>
          manager.id === updatedManager.id ? updatedManager : manager
        )
      } catch (error) {
        console.error('Error updating manager:', error)
        LNbits.utils.notifyError(error)
      } finally {
        this.closeManagerDialog()
      }
    },
    async deleteManager(id) {
      this.$q
        .dialog({
          title: 'Confirm Deletion',
          message: 'Are you sure you want to delete this manager?',
          cancel: true,
          persistent: true
        })
        .onOk(async () => {
          try {
            await LNbits.api.request(
              'DELETE',
              `/inventory/api/v1/managers/${id}`
            )
            this.managers = this.managers.filter(manager => manager.id !== id)
          } catch (error) {
            console.error('Error deleting manager:', error)
            LNbits.utils.notifyError(error)
          }
        })
    },
    async getManagerItems(managerId) {
      return await this.getItemsPaginated({
        pagination: {...this.itemsTable.pagination},
        filter: {manager_id: managerId, is_approved: false}
      })
    },
    showServiceDialog(id) {
      this.serviceDialog.show = true
      if (id) {
        const service = this.services.find(svc => svc.id === id)
        this.serviceDialog.data = {...service}
        return
      }
      this.serviceDialog.data = {}
    },
    submitServiceData() {
      const data = this.serviceDialog.data
      data.inventory_id = this.openInventory
      if (data.tags && Array.isArray(data.tags)) {
        data.tags = data.tags.join(',')
      }
      if (data.id) {
        this.updateService(data)
      } else {
        this.createService(data)
      }
    },
    async getServices() {
      try {
        const {data} = await LNbits.api.request(
          'GET',
          `/inventory/api/v1/services/${this.openInventory}`
        )
        this.services = [...data].map(service => {
          if (service.tags && typeof service.tags === 'string') {
            service.tags = service.tags.split(',').map(tag => tag.trim())
          } else {
            service.tags = []
          }
          return service
        })
      } catch (error) {
        console.error('Error fetching services:', error)
        LNbits.utils.notifyError(error)
      }
    },
    async updateService(data) {
      try {
        const {data: updatedService} = await LNbits.api.request(
          'PUT',
          `/inventory/api/v1/services/${data.id}`,
          null,
          data
        )
        this.services = this.services.map(service =>
          service.id === updatedService.id ? updatedService : service
        )
        console.log('Service updated:', updatedService)
      } catch (error) {
        console.error('Error updating service:', error)
        LNbits.utils.notifyError(error)
      } finally {
        this.closeServiceDialog()
      }
    },
    async createService(data) {
      try {
        const {data: createdService} = await LNbits.api.request(
          'POST',
          `/inventory/api/v1/services`,
          null,
          data
        )
        this.services = [...this.services, createdService]
        console.log('Service created:', createdService)
      } catch (error) {
        console.error('Error creating service:', error)
        LNbits.utils.notifyError(error)
      } finally {
        this.closeServiceDialog()
      }
    },
    async deleteService(id) {
      this.$q
        .dialog({
          title: 'Confirm Deletion',
          message: 'Are you sure you want to delete this service?',
          cancel: true,
          persistent: true
        })
        .onOk(async () => {
          try {
            await LNbits.api.request(
              'DELETE',
              `/inventory/api/v1/services/${id}`
            )
            this.services = this.services.filter(service => service.id !== id)
          } catch (error) {
            console.error('Error deleting service:', error)
            LNbits.utils.notifyError(error)
          }
        })
    },
    async getStockLogsPaginated(props) {
      console.log('Getting paginated stock logs with props:', props)
      console.log('Current stockLogsTable state:', this.stockLogsTable)
      try {
        const params = LNbits.utils.prepareFilterQuery(
          this.stockLogsTable,
          props
        )
        const {data} = await LNbits.api.request(
          'GET',
          `/inventory/api/v1/logs/${this.openInventory}/paginated?${params}`
        )
        this.logs = [...data.data]
        this.stockLogsTable.pagination.rowsNumber = data.total
      } catch (error) {
        console.error('Error fetching stock logs:', error)
        LNbits.utils.notifyError(error)
      }
    },
    async fetchCurrencies() {
      try {
        const response = await LNbits.api.request('GET', '/api/v1/currencies')
        this.currencyOptions = ['sat', ...response.data]
      } catch (error) {
        LNbits.utils.notifyApiError(error)
      }
    }
  },
  // To run on startup
  async created() {
    this.itemGrid = this.$q.localStorage.getItem('lnbits_inventoryItemGrid')
    await this.fetchCurrencies()
    await this.getInventories()
  }
})
