import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const bannersDir = path.join(__dirname, '../public/images/banners');
const manifestPath = path.join(__dirname, '../src/banner-manifest.js');

// Read all image files from the banners directory
const files = fs.readdirSync(bannersDir).filter(file => {
  const ext = path.extname(file).toLowerCase();
  return ['.jpg', '.jpeg', '.png', '.webp'].includes(ext);
});

// Generate manifest as JavaScript module
const sortedFiles = files.sort();
const manifestContent = `// Auto-generated file - do not edit manually
// Run 'npm run generate-banners' to update this file

export default {
  banners: ${JSON.stringify(sortedFiles, null, 2)}
};
`;

// Write manifest file
fs.writeFileSync(manifestPath, manifestContent);

console.log(`Generated banner manifest with ${files.length} images:`, sortedFiles);
