window.app.component('photo-gallery-form', {
  name: 'photo-gallery-form',
  props: {
    modelValue: {
      type: Array,
      default: () => []
    },
    max: {
      type: Number,
      default: 5
    },
    maxWidth: {
      type: Number,
      default: 800
    }
  },

  emits: ['update:modelValue'],

  data() {
    return {
      inputKey: 0 // force re-render input when needed
    }
  },

  computed: {
    gallery: {
      get() {
        return this.modelValue
      },
      set(val) {
        this.$emit('update:modelValue', val)
      }
    },
    canAdd() {
      return this.gallery.length < this.max
    }
  },

  methods: {
    async resizePhoto(file) {
      return new Promise((resolve, reject) => {
        const img = new Image()
        const reader = new FileReader()

        reader.onload = e => (img.src = e.target.result)
        img.onload = () => {
          const canvas = document.createElement('canvas')
          let w = img.width,
            h = img.height
          if (w > this.maxWidth) {
            h = (this.maxWidth / w) * h
            w = this.maxWidth
          }

          canvas.width = w
          canvas.height = h
          const ctx = canvas.getContext('2d')
          ctx.drawImage(img, 0, 0, w, h)

          canvas.toBlob(
            blob => {
              const resized = new File([blob], file.name, {
                type: 'image/jpeg',
                lastModified: Date.now()
              })
              resolve(resized)
            },
            'image/jpeg',
            0.7
          )
        }
        reader.onerror = reject
        reader.readAsDataURL(file)
      })
    },

    async onFileChange(e) {
      const file = e.target.files[0]
      if (!file) return

      if (!this.canAdd) {
        LNbits.utils.notifyError(`Maximum ${this.max} photos allowed`)
        return
      }

      try {
        const resized = await this.resizePhoto(file)
        const preview = URL.createObjectURL(resized)
        this.gallery.push({
          file: resized,
          preview,
          assetId: null,
          isNew: true
        })
        this.inputKey++
      } catch (err) {
        LNbits.utils.notifyError('Failed to process image')
      }
    },

    addFromUrl() {
      if (!this.canAdd) {
        LNbits.utils.notifyError(`Maximum ${this.max} photos allowed`)
        return
      }

      this.$q
        .dialog({
          title: 'Add Photo from URL',
          color: 'secondary',
          prompt: {
            model: '',
            type: 'text',
            isValid: isURLimg,
            label: 'Image URL',
            attrs: {
              placeholder: 'https://example.com/photo.jpg'
            }
          },
          cancel: true,
          persistent: true
        })
        .onOk(url => {
          const preview = url.trim()
          this.gallery.push({
            file: null,
            preview,
            assetId: null,
            isNew: true
          })
        })
    },

    remove(index) {
      URL.revokeObjectURL(this.gallery[index].preview)
      this.gallery.splice(index, 1)
      this.inputKey--
    },
    created() {}
  },

  template: `
    <div>
    <div class="float-right">
    <q-btn
    outline
    color="secondary"
    class="q-mb-sm q-mr-sm"
    :disable="!canAdd"
    label="Add URL"
    @click="addFromUrl"
    ></q-btn>
    <q-btn
    label="Add Photo"
    color="secondary"
    :disable="!canAdd"
    @click="$refs.fileInput.click()"
    class="q-mb-sm"
    ></q-btn>
        <div class="text-right text-caption" v-text="gallery.length + ' / ' + max">
        </div>
    </div>

      <input
        :key="inputKey"
        ref="fileInput"
        type="file"
        accept="image/*"
        style="display:none"
        @change="onFileChange"
      >

      <div class="row q-gutter-xs q-mt-sm">
        <div v-for="(p, i) in gallery" :key="i" class="relative-position">
          <img
            :src="p.preview"
            style="width:80px;height:80px;object-fit:cover;border-radius:6px"
          >
          <q-btn
            round dense flat icon="close" size="xs"
            class="absolute-top-right"
            style="margin:2px"
            @click="remove(i)"
          />
        </div>
      </div>
    </div>
  `
})
