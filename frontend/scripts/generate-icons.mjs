import sharp from 'sharp'
import { readFileSync, mkdirSync } from 'fs'
import { dirname, join } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const iconsDir = join(__dirname, '../public/icons')
const svg = readFileSync(join(iconsDir, 'icon.svg'))

mkdirSync(iconsDir, { recursive: true })

const sizes = [72, 96, 128, 144, 152, 192, 384, 512]

for (const size of sizes) {
  await sharp(svg)
    .resize(size, size)
    .png()
    .toFile(join(iconsDir, `icon-${size}.png`))
}

await sharp(svg)
  .resize(512, 512)
  .png()
  .toFile(join(iconsDir, 'icon.png'))

console.log('Generated PWA icons:', sizes.map((s) => `icon-${s}.png`).join(', '))
