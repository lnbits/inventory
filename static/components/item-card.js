window.app.component('item-card', {
  name: 'item-card',
  props: {
    item: {
      type: Object,
      required: true
    },
    currency: {
      type: String,
      required: true
    }
  },
  data() {
    return {}
  },
  computed: {
    chipColor() {
      if (!this.item.quantity_in_stock) return 'grey'
      return this.item.quantity_in_stock <= this.item.reorder_threshold
        ? 'red'
        : 'green'
    },
    computePrice() {
      const isSat = ['sat', 'sats'].includes((this.currency || '').toLowerCase())
      if (isSat) {
        return this.item.price ? `${this.item.price} sats` : 'Free'
      }
      return this.item.price
        ? LNbits.utils.formatCurrency(this.item.price, this.currency)
        : 'Free'
    },
    stockText() {
      if (!this.item.quantity_in_stock) return 'Out of Stock'
      if (this.item.quantity_in_stock <= this.item.reorder_threshold)
        return 'Low Stock'
      return 'In Stock'
    },
    itemImgUrl() {
      return isBase64String(this.item.images[0])
        ? this.item.images[0]
        : `/api/v1/assets/${this.item.images[0]}/thumbnail`
    }
  },
  methods: {},
  created() {},
  template: `
  <q-card class="flex column full-height" clickable>
      <q-card-section horizontal class="text-section">
        <div v-if="item.images && item.images.length" class="col-4 flex items-center justify-center">
          <q-img
            height="100%" width="100%" fit="cover"
            :src="itemImgUrl"
            placeholder-src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAJYAAACWBAMAAADOL2zRAAAAG1BMVEXMzMyWlpaqqqq3t7fFxcW+vr6xsbGjo6OcnJyLKnDGAAAACXBIWXMAAA7EAAAOxAGVKw4bAAABAElEQVRoge3SMW+DMBiE4YsxJqMJtHOTITPeOsLQnaodGImEUMZEkZhRUqn92f0MaTubtfeMh/QGHANEREREREREREREtIJJ0xbH299kp8l8FaGtLdTQ19HjofxZlJ0m1+eBKZcikd9PWtXC5DoDotRO04B9YOvFIXmXLy2jEbiqE6Df7DTleA5socLqvEFVxtJyrpZFWz/pHM2CVte0lS8g2eDe6prOyqPglhzROL+Xye4tmT4WvRcQ2/m81p+/rdguOi8Hc5L/8Qk4vhZzy08DduGt9eVQyP2qoTM1zi0/uf4hvBWf5c77e69Gf798y08L7j0RERERERERERH9P99ZpSVRivB/rgAAAABJRU5ErkJggg=="
          ></q-img>
        </div>

        <q-card-section class="overflow-hidden text-col">
          <div class="text-h6 ellipsis q-pb-md">
            <q-icon color="red" v-if="!item.is_active" class="q-mr-sm" name="link_off">
              <q-tooltip>Inactive Item</q-tooltip>
            </q-icon>
            <span v-text="item.name"></span>
          </div>
          <div class="q-pb-md description">
            <span class="text-subtitle1 ellipsis-3-lines" v-text="item.description"></span>
          </div>
          <div v-if="item.tags && item.tags.length" class="q-pb-sm">
            <q-chip
              v-for="tag in item.tags"
              :key="tag"
              dense
              color="primary"
              text-color="white"
              class="q-mr-xs q-mb-xs"
            >
              {{ tag }}
            </q-chip>
          </div>
          <div v-if="item.omit_tags && item.omit_tags.length" class="q-pb-sm">
            <q-chip
              v-for="tag in item.omit_tags"
              :key="tag"
              dense
              color="negative"
              text-color="white"
              class="q-mr-xs q-mb-xs bg-negative text-white"
            >
              {{ tag }}
            </q-chip>
          </div>
          <div class="text-subtitle1 text-justify">
            <div>
              <span>Price: </span>
              <span v-text="computePrice"></span>
            </div>
          </div>
        </q-card-section>
      </q-card-section>

      <q-separator></q-separator>

      <q-card-actions>
        <q-chip square>
          <div v-if="item.quantity_in_stock">
            <q-avatar :color="chipColor" text-color="white">
              <span v-text="item.quantity_in_stock"></span>
            </q-avatar>
            <span v-text="stockText"></span>
          </div>
        </q-chip>
        <div class="q-ml-auto">
          <q-btn flat size="sm" padding="md" color="grey-6" icon="edit" @click="$emit('edit')"></q-btn>
          <q-btn flat size="sm" padding="md" color="red" icon="delete" @click="$emit('delete')"></q-btn>
        </div>
      </q-card-actions>
    </q-card>
  `
})
