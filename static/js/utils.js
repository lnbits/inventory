function toCsv(arr, separator = ',') {
  return arr && arr.length ? arr.join(separator) : null
}
function fromCsv(str, separator = ',') {
  return str ? str.split(separator) : []
}

function mapItems(obj) {
  obj.price = Number(obj.price.toFixed(2))
  if (obj.discount_percentage) {
    obj.discount_percentage = Number(obj.discount_percentage.toFixed(2))
  }
  if (obj.discount_percentage) {
    obj.discount_percentage = Number(obj.discount_percentage.toFixed(2))
  }
  if (obj.unit_cost) {
    obj.unit_cost = Number(obj.unit_cost.toFixed(2))
  }
  if (obj.tax_rate) {
    obj.tax_rate = Number(obj.tax_rate.toFixed(2))
  }
  obj.tags = fromCsv(obj.tags)
  obj.omit_tags = fromCsv(obj.omit_tags)
  obj.images = isBase64String(obj.images)
    ? fromCsv(obj.images, '|||')
    : fromCsv(obj.images)
  return obj
}

function fileToBase64(file) {
  return new Promise(resolve => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.readAsDataURL(file)
  })
}

function base64ToFile(base64String, filename) {
  const arr = base64String.split(',')
  const mime = arr[0].match(/:(.*?);/)[1]
  const bstr = atob(arr[1])
  let n = bstr.length
  const u8arr = new Uint8Array(n)
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n)
  }
  return new File([u8arr], filename, {type: mime})
}

function isBase64String(str) {
  if (typeof str !== 'string') return false
  return str.includes('data:') && str.includes('base64')
}
