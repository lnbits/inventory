window.app = Vue.createApp({
  el: '#vue',
  mixins: [windowMixin],
  // Declare models/variables
  data() {
    return {
      tab: 'items',
      tabOptions: [
        {label: 'Items', value: 'items'},
        {label: 'Stock Managers', value: 'managers'},
        {label: 'Stock Logs', value: 'orders'},
        {label: 'Settings', value: 'settings'}
      ],
      currencyOptions: [],
      inventory: null,
      managers: [],
      managerTagLoading: {},
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
                : LNbits.utils.formatCurrency(
                    row.price,
                    this.openInventoryCurrency
                  )
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
            name: 'omit_tags',
            align: 'left',
            label: 'Omit Tags',
            field: 'omit_tags',
            sortable: true,
            format: val => (val ? val.toString() : '')
          },
          {
            name: 'created_at',
            align: 'left',
            label: 'Created At',
            field: 'created_at',
            format: val => LNbits.utils.formatDate(val),
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
      inventoryLoaded: false,
      importingItems: false,
      exportingItems: false,
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
            sortable: true,
            classes: 'text-primary cursor-pointer',
            style: 'text-decoration: underline',
            headerStyle: 'width: 220px'
          },
          {
            name: 'created_at',
            align: 'left',
            label: 'Created At',
            field: 'created_at',
            format: val => LNbits.utils.formatDate(val),
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
      } else if (newTab === 'orders') {
        await this.getStockLogsPaginated()
      }
    }
  },
  methods: {
    normalizeManager(manager) {
      const inventoryTags = this.inventory?.tags || []
      const rawTags = manager.tags
      let parsedTags = null
      if (rawTags === '' || rawTags === false) {
        parsedTags = []
      } else if (rawTags === null || rawTags === undefined) {
        parsedTags = null
      } else if (Array.isArray(rawTags)) {
        parsedTags = rawTags
      } else {
        parsedTags = fromCsv(rawTags)
      }
      return {
        ...manager,
        tags: parsedTags,
        selectedTags: parsedTags === null ? [...inventoryTags] : [...parsedTags]
      }
    },
    prepareManagerTags(selectedTags) {
      if (selectedTags === null) {
        return null
      }
      const tags = Array.isArray(selectedTags)
        ? selectedTags.filter(Boolean)
        : []
      const inventoryTags = this.inventory?.tags || []
      if (tags.length === 0) {
        return inventoryTags.length === 0 ? null : ''
      }
      const hasAllInventoryTags =
        inventoryTags.length &&
        tags.length === inventoryTags.length &&
        tags.every(tag => inventoryTags.includes(tag))
      if (hasAllInventoryTags) {
        return null
      }
      return toCsv(tags)
    },
    showInventoryDialog() {
      this.inventoryDialog.show = true
      if (this.inventory) {
        const tags =
          typeof this.inventory.tags === 'string'
            ? fromCsv(this.inventory.tags)
            : this.inventory.tags || []
        const omitTags =
          typeof this.inventory.omit_tags === 'string'
            ? fromCsv(this.inventory.omit_tags)
            : this.inventory.omit_tags || []
        this.inventoryDialog.data = {...this.inventory, tags}
        this.inventoryDialog.data.omit_tags = omitTags
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
      return
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
      const normalized =
        this.normalizeCurrency(currency) || this.defaultCurrency()
      this.openInventoryCurrency = normalized
      this.itemDialog.currency = normalized
    },
    checkIsSat(currency) {
      return ['sat', 'sats'].includes((currency || '').toLowerCase())
    },
    getCurrencyDecimals(currency) {
      const normalized =
        this.normalizeCurrency(currency) || this.defaultCurrency()
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
        const {data} = await LNbits.api.request('GET', '/inventory/api/v1')
        if (!data || (Array.isArray(data) && data.length === 0)) {
          this.inventory = null
          this.openInventory = null
          this.setInventoryCurrencies(null)
          this.items = []
          return
        }
        const inventoryData = Array.isArray(data) ? data[0] : data
        inventoryData.tags = fromCsv(inventoryData.tags)
        inventoryData.omit_tags = fromCsv(inventoryData.omit_tags)
        this.inventory = {...inventoryData} // Change to single inventory
        this.openInventory = this.inventory.id
        this.setInventoryCurrencies(this.inventory.currency)
        await this.getItemsPaginated()
        await this.getManagers()
      } catch (error) {
        console.error('Error fetching inventory:', error)
      } finally {
        this.inventoryLoaded = true
      }
    },
    submitInventoryData() {
      const data = this.inventoryDialog.data
      if (data.tags && Array.isArray(data.tags)) {
        data.tags = data.tags.join(',')
      }
      if (data.omit_tags && Array.isArray(data.omit_tags)) {
        data.omit_tags = data.omit_tags.join(',')
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
        createdInventory.omit_tags = fromCsv(createdInventory.omit_tags)
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
        updatedInventory.omit_tags = fromCsv(updatedInventory.omit_tags)
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
            await LNbits.api.request('DELETE', `/inventory/api/v1/${id}`)
            this.inventory = null
            this.openInventory = null
            this.items = []
            this.managers = []
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
      this.loadingItems = true
      try {
        const params = LNbits.utils.prepareFilterQuery(this.itemsTable, props)
        const {data} = await LNbits.api.request(
          'GET',
          `/inventory/api/v1/items/${this.openInventory}/paginated?${params}`
        )
        this.items = data.data.map(item => mapItems(item))
        this.itemsTable.pagination.rowsNumber = data.total
      } catch (error) {
        console.error('Error fetching items:', error)
        LNbits.utils.notifyError(error)
      } finally {
        this.loadingItems = false
      }
    },
    showItemDialog(id) {
      if (!this.inventory) return
      this.itemDialog.show = true
      this.setInventoryCurrencies(this.inventory?.currency)
      if (id) {
        const item = this.items.find(it => it.id === id)
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
      data.omit_tags = toCsv(data.omit_tags)
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
        this.managers = [...data].map(manager => this.normalizeManager(manager))
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
        const tagSelection =
          data.tags === undefined ? this.inventory?.tags ?? [] : data.tags
        const payload = {
          inventory_id: data.inventory_id,
          name: data.name,
          email: data.email,
          tags: this.prepareManagerTags(tagSelection)
        }
        const {data: createdManager} = await LNbits.api.request(
          'POST',
          `/inventory/api/v1/managers/${this.openInventory}`,
          null,
          payload
        )
        this.managers = [
          ...this.managers,
          this.normalizeManager(createdManager)
        ]
      } catch (error) {
        console.error('Error creating manager:', error)
        LNbits.utils.notifyError(error)
      } finally {
        this.closeManagerDialog()
      }
    },
    async updateManager(data) {
      try {
        const tagSelection = data.tags === undefined ? null : data.tags
        const payload = {
          inventory_id: data.inventory_id,
          name: data.name,
          email: data.email,
          tags: this.prepareManagerTags(tagSelection)
        }
        const {data: updatedManager} = await LNbits.api.request(
          'PUT',
          `/inventory/api/v1/managers/${data.id}`,
          null,
          payload
        )
        const normalizedManager = this.normalizeManager(updatedManager)
        this.managers = this.managers.map(manager =>
          manager.id === normalizedManager.id ? normalizedManager : manager
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
    async updateManagerTags(manager, selectedTags) {
      this.managerTagLoading = {
        ...this.managerTagLoading,
        [manager.id]: true
      }
      const payload = {
        inventory_id: manager.inventory_id,
        name: manager.name,
        email: manager.email,
        tags: this.prepareManagerTags(selectedTags)
      }
      try {
        const {data} = await LNbits.api.request(
          'PUT',
          `/inventory/api/v1/managers/${manager.id}`,
          null,
          payload
        )
        const normalized = this.normalizeManager(data)
        this.managers = this.managers.map(mgr =>
          mgr.id === normalized.id ? normalized : mgr
        )
      } catch (error) {
        console.error('Error updating manager tags:', error)
        LNbits.utils.notifyError(error)
      } finally {
        this.managerTagLoading = {
          ...this.managerTagLoading,
          [manager.id]: false
        }
      }
    },
    async getManagerItems(managerId) {
      return await this.getItemsPaginated({
        pagination: {...this.itemsTable.pagination},
        filter: {manager_id: managerId, is_approved: false}
      })
    },
    showServiceDialog(id) {
      return
    },
    submitServiceData() {
      return
    },
    async getStockLogsPaginated(props) {
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
    triggerImportItems() {
      if (!this.openInventory) {
        LNbits.utils.notifyError('No inventory selected')
        return
      }
      this.$refs.importItemsInput && this.$refs.importItemsInput.click()
    },
    async handleImportFile(event) {
      const file = event?.target?.files?.[0]
      if (!file) return
      this.importingItems = true
      try {
        const text = await file.text()
        const parsed = JSON.parse(text)
        const items = Array.isArray(parsed) ? parsed : parsed.items
        if (!Array.isArray(items) || !items.length) {
          throw new Error('No items found in the selected file')
        }
        await LNbits.api.request(
          'POST',
          `/inventory/api/v1/items/${this.openInventory}/import`,
          null,
          {items}
        )
        await this.getItemsPaginated()
        this.$q.notify({
          type: 'positive',
          message: `Imported ${items.length} item${items.length === 1 ? '' : 's'}.`
        })
      } catch (error) {
        console.error('Error importing items:', error)
        const message =
          error?.response?.data?.detail ||
          error?.message ||
          'Failed to import items.'
        LNbits.utils.notifyError(message)
      } finally {
        this.importingItems = false
        if (event?.target) {
          event.target.value = ''
        }
      }
    },
    async exportItems() {
      if (!this.openInventory) {
        LNbits.utils.notifyError('No inventory selected')
        return
      }
      this.exportingItems = true
      try {
        const {data} = await LNbits.api.request(
          'GET',
          `/inventory/api/v1/items/${this.openInventory}/export`
        )
        const items = Array.isArray(data?.items) ? data.items : []
        const blob = new Blob([JSON.stringify(items, null, 2)], {
          type: 'application/json'
        })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        const timestamp = new Date()
          .toISOString()
          .slice(0, 19)
          .replace(/[:T]/g, '-')
        link.download = `inventory-${this.openInventory}-items-${timestamp}.json`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
        this.$q.notify({type: 'positive', message: 'Items exported as JSON.'})
      } catch (error) {
        console.error('Error exporting items:', error)
        const message =
          error?.response?.data?.detail ||
          error?.message ||
          'Failed to export items.'
        LNbits.utils.notifyError(message)
      } finally {
        this.exportingItems = false
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
