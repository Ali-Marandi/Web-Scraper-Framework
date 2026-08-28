---
name: image-edit
description: Implement AI image editing and modification capabilities using the z-ai-web-dev-sdk. Use this skill when the user needs to edit existing images, create variations, modify visual content, redesign assets, or transform images based on text descriptions. Supports multiple image sizes and returns base64 encoded results. Also includes CLI tool for quick image editing.
license: MIT
---

# Image Edit Skill

This skill guides the implementation of image editing and modification functionality using the z-ai-web-dev-sdk package and CLI tool, enabling intelligent transformation and editing of images based on text descriptions.

## Skills Path

**Skill Location**: `{project_path}/skills/image-edit`

this skill is located at above path in your project.

**Reference Scripts**: Example test scripts are available in the `{Skill Location}/scripts/` directory for quick testing and reference. See `{Skill Location}/scripts/image-edit.ts` for a working example.

## Overview

Image Edit allows you to build applications that modify, transform, and enhance existing images using AI models. Perfect for redesigning assets, creating variations, improving visual content, and transforming images based on textual descriptions.

**IMPORTANT**: z-ai-web-dev-sdk MUST be used in backend code only. Never use it in client-side code.

## SDK API Method

The image editing functionality uses the following API method:

```javascript
await zai.images.generations.edit({
  prompt: string,              // Required: Description of the edit to apply
  images: [{ url: string }],  // Required: Array with image URL or base64 data URL
  size?: string,              // Optional: Output size (default: '1024x1024')
  model?: string              // Optional: Model name
})
```

**Important**: The `images` parameter must be an array of objects with a `url` property, not a plain string.

**API Endpoint**: `POST /images/generations/edit`

**Returns**: `ImageGenerationResponse` with base64 encoded edited image

## Prerequisites

The z-ai-web-dev-sdk package is already installed. Import it as shown in the examples below.

## Basic Image Editing

### Simple Image Transformation

```javascript
import ZAI from 'z-ai-web-dev-sdk';
import fs from 'fs';

async function editImage(imageSource, editPrompt, outputPath, size = '1024x1024') {
  const zai = await ZAI.create();

  const response = await zai.images.generations.edit({
    prompt: editPrompt,
    images: [{ url: imageSource }],  // Array of objects with url property
    size: size
  });

  const imageBase64 = response.data[0].base64;
  
  // Save edited image
  const buffer = Buffer.from(imageBase64, 'base64');
  fs.writeFileSync(outputPath, buffer);
  
  console.log(`Edited image saved to ${outputPath}`);
  return outputPath;
}

// Usage - Using remote image URL
await editImage(
  'https://example.com/landscape.jpg',
  'Transform this landscape into a night scene with stars and moon',
  './landscape_night.png'
);

// Usage - Using local image converted to base64
import { readFileSync } from 'fs';
const imageBuffer = readFileSync('./photo.jpg');
const base64Image = imageBuffer.toString('base64');
const dataUrl = `data:image/jpeg;base64,${base64Image}`;

await editImage(
  dataUrl,
  'Change the cat to a dog, keep everything else the same',
  './dog_version.png'
);
```

### Create Image Variations

```javascript
import ZAI from 'z-ai-web-dev-sdk';
import fs from 'fs';

async function createVariation(imageSource, baseDescription, variation, outputPath, size = '1024x1024') {
  const zai = await ZAI.create();

  // Combine base description with variation request
  const prompt = `${baseDescription}, ${variation}`;

  const response = await zai.images.generations.edit({
    prompt: prompt,
    images: [{ url: imageSource }],
    size: size
  });

  const imageBase64 = response.data[0].base64;
  const buffer = Buffer.from(imageBase64, 'base64');
  fs.writeFileSync(outputPath, buffer);

  return {
    path: outputPath,
    prompt: prompt,
    variation: variation
  };
}

// Usage - Create variations from original image
await createVariation(
  'https://example.com/headshot.jpg',
  'Professional headshot photo',
  'with blue background instead of gray',
  './headshot_blue.png'
);

await createVariation(
  './smartphone.png',
  'Product photo of smartphone',
  'on wooden table instead of white background',
  './product_wood.png'
);
```

### Multiple Image Sizes for Editing

```javascript
import ZAI from 'z-ai-web-dev-sdk';
import fs from 'fs';

// Supported sizes
const SUPPORTED_SIZES = [
  '1024x1024',  // Square
  '768x1344',   // Portrait
  '864x1152',   // Portrait
  '1344x768',   // Landscape
  '1152x864',   // Landscape
  '1440x720',   // Wide landscape
  '720x1440'    // Tall portrait
];

async function editImageWithSize(imageSource, editPrompt, size, outputPath) {
  if (!SUPPORTED_SIZES.includes(size)) {
    throw new Error(`Unsupported size: ${size}. Use one of: ${SUPPORTED_SIZES.join(', ')}`);
  }

  const zai = await ZAI.create();

  const response = await zai.images.generations.edit({
    prompt: editPrompt,
    images: [{ url: imageSource }],
    size: size
  });

  const imageBase64 = response.data[0].base64;
  const buffer = Buffer.from(imageBase64, 'base64');
  fs.writeFileSync(outputPath, buffer);

  return {
    path: outputPath,
    size: size,
    fileSize: buffer.length
  };
}

// Usage - Edit with different aspect ratios
await editImageWithSize(
  './logo.png',
  'Redesign the logo to be more modern and minimalist',
  '1024x1024',
  './logo_redesigned.png'
);

await editImageWithSize(
  'https://example.com/portrait.jpg',
  'Transform the portrait to landscape orientation, sunset lighting',
  '1344x768',
  './portrait_landscape.png'
);
```

## CLI Tool Usage

The z-ai CLI tool provides a convenient way to edit images directly from the command line.

### Basic CLI Usage

```bash
# Edit image with full options
z-ai image-edit --prompt "Change the background to sunset colors" --image "./photo.png" --output "./edited.png"

# Short form
z-ai image-edit -p "Make it darker and moodier" -i "./original.jpg" -o "./moody.png"

# Specify output size
z-ai image-edit -p "Redesign in modern style" -i "./design.png" -o "./modern.png" -s 1344x768

# Using remote image URL
z-ai image-edit -p "Convert to landscape orientation" -i "https://example.com/photo.png" -o "./landscape.png" -s 1344x768
```

### CLI Parameters

- `--prompt, -p`: **Required** - Description of the edit to apply
- `--image, -i`: **Required** - Original image URL or local file path
- `--output, -o`: **Required** - Output image file path (PNG format)
- `--size, -s`: Optional - Image size, default is 1024x1024
- `--help, -h`: Optional - Display help information

### Supported Sizes

- `1024x1024`, `768x1344`, `864x1152`, `1344x768`, `1152x864`, `1440x720`, `720x1440`

### CLI Use Cases for Image Editing

```bash
# Redesign existing asset
z-ai image-edit -p "Redesign the logo with gradients and modern styling" -i "./logo.png" -o "./logo_v2.png" -s 1024x1024

# Change color scheme
z-ai image-edit -p "Change color scheme to blue and white, professional style" -i "./original.png" -o "./recolored.png" -s 1440x720

# Style transformation
z-ai image-edit -p "Transform to oil painting style, vibrant colors" -i "./photo.jpg" -o "./oil_painting.png" -s 1152x864

# Background replacement
z-ai image-edit -p "Replace background with modern office setting" -i "./portrait.png" -o "./new_background.png" -s 1344x768

# Lighting adjustment
z-ai image-edit -p "Adjust to golden hour lighting, warm tones" -i "./landscape.jpg" -o "./golden_hour.png" -s 1024x1024

# Element modification
z-ai image-edit -p "Replace the red car with a blue motorcycle" -i "./scene.png" -o "./modified.png" -s 1344x768

# Mood transformation
z-ai image-edit -p "Transform to dark moody atmosphere with dramatic lighting" -i "./bright.jpg" -o "./moody.png" -s 1440x720

# Using remote image URL
z-ai image-edit -p "Add a hat to the person" -i "https://example.com/photo.png" -o "./result.png" -s 1024x1024
```

## Advanced Use Cases

### Batch Image Editing

```javascript
import ZAI from 'z-ai-web-dev-sdk';
import fs from 'fs';
import path from 'path';

async function batchEditImages(editInstructions, outputDir, size = '1024x1024') {
  const zai = await ZAI.create();

  // Ensure output directory exists
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const results = [];

  for (let i = 0; i < editInstructions.length; i++) {
    try {
      const instruction = editInstructions[i];
      const filename = `edited_${i + 1}.png`;
      const outputPath = path.join(outputDir, filename);

      const response = await zai.images.generations.edit({
        prompt: instruction.prompt,
        images: [{ url: instruction.imageSource }],
        size: size
      });

      const imageBase64 = response.data[0].base64;
      const buffer = Buffer.from(imageBase64, 'base64');
      fs.writeFileSync(outputPath, buffer);

      results.push({
        success: true,
        instruction: instruction.prompt,
        path: outputPath,
        size: buffer.length
      });

      console.log(`✓ Edited: ${filename}`);
    } catch (error) {
      results.push({
        success: false,
        instruction: editInstructions[i].prompt,
        error: error.message
      });

      console.error(`✗ Failed: ${editInstructions[i].prompt} - ${error.message}`);
    }
  }

  return results;
}

// Usage - Create multiple variations from the same image
const editInstructions = [
  { 
    imageSource: './original.jpg',
    prompt: 'Change background to blue gradient' 
  },
  { 
    imageSource: './original.jpg',
    prompt: 'Transform to black and white, high contrast' 
  },
  { 
    imageSource: './original.jpg',
    prompt: 'Add sunset lighting effects' 
  }
];

const results = await batchEditImages(editInstructions, './edited-images');
console.log(`Edited ${results.filter(r => r.success).length} images`);
```

### Image Editing Service

```javascript
import ZAI from 'z-ai-web-dev-sdk';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

class ImageEditingService {
  constructor(outputDir = './edited-images') {
    this.outputDir = outputDir;
    this.zai = null;
    this.editHistory = [];
  }

  async initialize() {
    this.zai = await ZAI.create();
    
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  generateFilename(editPrompt) {
    const hash = crypto
      .createHash('md5')
      .update(`${editPrompt}-${Date.now()}`)
      .digest('hex')
      .substring(0, 8);
    
    return `edited_${hash}.png`;
  }

  async edit(imageSource, editPrompt, options = {}) {
    const {
      size = '1024x1024',
      saveToHistory = true,
      filename = null
    } = options;

    const response = await this.zai.images.generations.edit({
      prompt: editPrompt,
      images: [{ url: imageSource }],
      size: size
    });

    const imageBase64 = response.data[0].base64;
    const buffer = Buffer.from(imageBase64, 'base64');

    // Determine output path
    const outputFilename = filename || this.generateFilename(editPrompt);
    const outputPath = path.join(this.outputDir, outputFilename);

    fs.writeFileSync(outputPath, buffer);

    const result = {
      path: outputPath,
      imageSource: imageSource,
      editPrompt: editPrompt,
      size: size,
      fileSize: buffer.length,
      timestamp: new Date().toISOString()
    };

    // Save to history
    if (saveToHistory) {
      this.editHistory.push(result);
    }

    return result;
  }

  async createVariations(imageSource, basePrompt, variations, options = {}) {
    const results = [];
    
    for (const variation of variations) {
      const fullPrompt = `${basePrompt}, ${variation}`;
      const result = await this.edit(imageSource, fullPrompt, options);
      result.variation = variation;
      results.push(result);
    }

    return results;
  }

  getEditHistory() {
    return this.editHistory;
  }

  clearHistory() {
    this.editHistory = [];
  }
}

// Usage
const service = new ImageEditingService();
await service.initialize();

// Single edit
const edited = await service.edit(
  './original.jpg',
  'Transform to watercolor painting style',
  { size: '1024x1024' }
);

// Multiple variations from the same image
const variations = await service.createVariations(
  'https://example.com/product.png',
  'Professional product photo',
  [
    'with blue background',
    'with wooden surface',
    'with dramatic lighting'
  ]
);

console.log('Edit history:', service.getEditHistory());
```

### Style Transfer and Transformation

```javascript
import ZAI from 'z-ai-web-dev-sdk';
import fs from 'fs';

async function applyStyleTransfer(imageSource, content, style, outputPath, size = '1024x1024') {
  const zai = await ZAI.create();

  const prompt = `${content} transformed into ${style} style, maintain composition and subject`;

  const response = await zai.images.generations.edit({
    prompt: prompt,
    images: [{ url: imageSource }],
    size: size
  });

  const imageBase64 = response.data[0].base64;
  const buffer = Buffer.from(imageBase64, 'base64');
  fs.writeFileSync(outputPath, buffer);

  return {
    path: outputPath,
    content: content,
    style: style
  };
}

// Usage - Apply different styles to the same image
await applyStyleTransfer(
  './portrait.jpg',
  'Portrait photograph',
  'oil painting',
  './portrait_oil.png'
);

await applyStyleTransfer(
  'https://example.com/city.jpg',
  'City landscape',
  'watercolor',
  './city_watercolor.png'
);

await applyStyleTransfer(
  './product.png',
  'Product photo',
  'minimalist illustration',
  './product_minimal.png'
);
```

### Element Replacement

```javascript
import ZAI from 'z-ai-web-dev-sdk';
import fs from 'fs';

async function replaceElement(imageSource, baseScene, replaceWhat, replaceWith, outputPath, size = '1024x1024') {
  const zai = await ZAI.create();

  const prompt = `${baseScene}, replace ${replaceWhat} with ${replaceWith}, keep everything else identical`;

  const response = await zai.images.generations.edit({
    prompt: prompt,
    images: [{ url: imageSource }],
    size: size
  });

  const imageBase64 = response.data[0].base64;
  const buffer = Buffer.from(imageBase64, 'base64');
  fs.writeFileSync(outputPath, buffer);

  return {
    path: outputPath,
    modification: `${replaceWhat} → ${replaceWith}`
  };
}

// Usage
await replaceElement(
  './workspace.jpg',
  'Office workspace with laptop',
  'laptop',
  'desktop computer with dual monitors',
  './workspace_desktop.png'
);

await replaceElement(
  'https://example.com/living-room.jpg',
  'Living room interior with sofa',
  'blue sofa',
  'brown leather sofa',
  './living_room_leather.png'
);
```

## Best Practices

### 1. Effective Edit Prompts

```javascript
function buildEditPrompt(baseDescription, modification, preserveElements = []) {
  const components = [
    baseDescription,
    modification
  ];

  if (preserveElements.length > 0) {
    components.push(`keep ${preserveElements.join(', ')} unchanged`);
  }

  components.push('maintain overall composition');

  return components.filter(Boolean).join(', ');
}

// Usage
const editPrompt = buildEditPrompt(
  'Professional headshot photo',
  'change background to modern office',
  ['lighting', 'pose', 'expression']
);

// Result: "Professional headshot photo, change background to modern office, keep lighting, pose, expression unchanged, maintain overall composition"
```

### 2. Size Selection for Different Edit Types

```javascript
function selectSizeForEdit(editType) {
  const sizeMap = {
    'background-change': '1440x720',
    'style-transfer': '1024x1024',
    'color-adjustment': '1024x1024',
    'element-replacement': '1344x768',
    'composition-change': '1152x864',
    'portrait-edit': '768x1344',
    'landscape-edit': '1344x768'
  };

  return sizeMap[editType] || '1024x1024';
}

// Usage
const size = selectSizeForEdit('background-change');
await editImage('Replace background with beach scene', './beach_bg.png', size);
```

### 3. Error Handling with Retry

```javascript
import ZAI from 'z-ai-web-dev-sdk';
import fs from 'fs';

async function safeEditImage(imageSource, editPrompt, size, outputPath, retries = 3) {
  let lastError;

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const zai = await ZAI.create();

      const response = await zai.images.generations.edit({
        prompt: editPrompt,
        images: [{ url: imageSource }],
        size: size
      });

      if (!response.data || !response.data[0] || !response.data[0].base64) {
        throw new Error('Invalid response from image editing API');
      }

      const imageBase64 = response.data[0].base64;
      const buffer = Buffer.from(imageBase64, 'base64');
      fs.writeFileSync(outputPath, buffer);

      return {
        success: true,
        path: outputPath,
        attempts: attempt
      };
    } catch (error) {
      lastError = error;
      console.error(`Attempt ${attempt} failed:`, error.message);

      if (attempt < retries) {
        // Wait before retry (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
      }
    }
  }

  return {
    success: false,
    error: lastError.message,
    attempts: retries
  };
}
```

## Common Image Editing Use Cases

1. **Background Replacement**: Change or remove backgrounds in photos
2. **Style Transformation**: Convert photos to paintings, illustrations, etc.
3. **Color Adjustment**: Change color schemes, saturation, mood
4. **Element Modification**: Replace or modify specific elements
5. **Composition Changes**: Adjust framing, orientation, layout
6. **Lighting Adjustments**: Modify lighting, shadows, highlights
7. **Asset Redesign**: Modernize or rebrand existing designs
8. **Quality Enhancement**: Improve overall visual quality
9. **Variation Creation**: Generate multiple versions of an image
10. **Format Conversion**: Transform between different styles or formats

## Integration Examples

### Express.js API Endpoint

```javascript
import express from 'express';
import ZAI from 'z-ai-web-dev-sdk';
import fs from 'fs';
import path from 'path';

const app = express();
app.use(express.json());
app.use('/edited-images', express.static('edited-images'));

let zaiInstance;
const outputDir = './edited-images';

async function initZAI() {
  zaiInstance = await ZAI.create();
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
}

app.post('/api/edit-image', async (req, res) => {
  try {
    const { 
      imageSource,           // URL or base64 data URL
      editPrompt, 
      size = '1024x1024', 
      baseDescription = '' 
    } = req.body;

    if (!imageSource || !editPrompt) {
      return res.status(400).json({ 
        error: 'imageSource and editPrompt are required' 
      });
    }

    // Combine base description with edit instruction
    const fullPrompt = baseDescription 
      ? `${baseDescription}, ${editPrompt}`
      : editPrompt;

    const response = await zaiInstance.images.generations.edit({
      prompt: fullPrompt,
      images: [{ url: imageSource }],
      size: size
    });

    const imageBase64 = response.data[0].base64;
    const buffer = Buffer.from(imageBase64, 'base64');
    
    const filename = `edited_${Date.now()}.png`;
    const filepath = path.join(outputDir, filename);
    fs.writeFileSync(filepath, buffer);

    res.json({
      success: true,
      imageUrl: `/edited-images/${filename}`,
      editPrompt: fullPrompt,
      size: size
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/create-variations', async (req, res) => {
  try {
    const { 
      imageSource,      // URL or base64 data URL
      baseDescription, 
      variations, 
      size = '1024x1024' 
    } = req.body;

    if (!imageSource || !baseDescription || !variations || !Array.isArray(variations)) {
      return res.status(400).json({ 
        error: 'imageSource, baseDescription and variations array are required' 
      });
    }

    const results = [];

    for (const variation of variations) {
      const fullPrompt = `${baseDescription}, ${variation}`;

      const response = await zaiInstance.images.generations.edit({
        prompt: fullPrompt,
        images: [{ url: imageSource }],
        size: size
      });

      const imageBase64 = response.data[0].base64;
      const buffer = Buffer.from(imageBase64, 'base64');
      
      const filename = `variation_${Date.now()}_${Math.random().toString(36).substr(2, 9)}.png`;
      const filepath = path.join(outputDir, filename);
      fs.writeFileSync(filepath, buffer);

      results.push({
        variation: variation,
        imageUrl: `/edited-images/${filename}`
      });
    }

    res.json({
      success: true,
      results: results
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

initZAI().then(() => {
  app.listen(3000, () => {
    console.log('Image editing API running on port 3000');
  });
});
```

## CLI Integration in Scripts

### Shell Script for Batch Editing

```bash
#!/bin/bash

# Batch edit images with different styles
echo "Creating style variations..."

ORIGINAL_IMAGE="./product.jpg"
BASE="Professional product photo of laptop"

z-ai image-edit -p "$BASE, modern minimalist style, white background" -i "$ORIGINAL_IMAGE" -o "./variations/minimal.png" -s 1024x1024
z-ai image-edit -p "$BASE, dramatic lighting, dark background" -i "$ORIGINAL_IMAGE" -o "./variations/dramatic.png" -s 1024x1024
z-ai image-edit -p "$BASE, on wooden desk, natural lighting" -i "$ORIGINAL_IMAGE" -o "./variations/natural.png" -s 1024x1024

echo "Variations created successfully!"
```

## Troubleshooting

**Issue**: "SDK must be used in backend"
- **Solution**: Ensure z-ai-web-dev-sdk is only used in server-side code

**Issue**: Invalid size parameter
- **Solution**: Use only supported sizes: 1024x1024, 768x1344, 864x1152, 1344x768, 1152x864, 1440x720, 720x1440

**Issue**: Edited image doesn't match intention
- **Solution**: Be more specific in edit prompts. Include what to change AND what to preserve

**Issue**: CLI command not found
- **Solution**: Ensure z-ai CLI is properly installed and in PATH

**Issue**: Image quality loss after editing
- **Solution**: Use larger size options and include quality terms in prompts

**Issue**: Inconsistent results across variations
- **Solution**: Include more specific base description and detailed modification instructions

## Edit Prompt Engineering Tips

### Good Edit Prompts
- ✓ "Change background to modern office, keep subject and lighting identical"
- ✓ "Transform to watercolor style, maintain composition and colors"
- ✓ "Replace red car with blue motorcycle, keep road and scenery unchanged"
- ✓ "Adjust to golden hour lighting, preserve all elements"

### Poor Edit Prompts
- ✗ "make it better"
- ✗ "change something"
- ✗ "different version"

### Edit Prompt Components
1. **Base Context**: What the image currently represents
2. **Modification**: What specific changes to make
3. **Preservation**: What elements to keep unchanged
4. **Quality**: Desired output quality or style

### Effective Edit Patterns

**Background Changes:**
```
"[Subject description], replace background with [new background], maintain subject lighting and pose"
```

**Style Transfers:**
```
"[Current description] transformed into [style name] style, preserve composition and key elements"
```

**Element Replacement:**
```
"[Scene description], replace [element A] with [element B], keep everything else identical"
```

**Color Adjustments:**
```
"[Image description], change color scheme to [colors], maintain contrast and composition"
```

## Supported Image Sizes

- `1024x1024` - Square (Best for general editing)
- `768x1344` - Portrait
- `864x1152` - Portrait
- `1344x768` - Landscape
- `1152x864` - Landscape
- `1440x720` - Wide landscape
- `720x1440` - Tall portrait

## Remember

- Always use z-ai-web-dev-sdk in backend code only
- The SDK is already installed - import as shown
- CLI tool is available for quick image editing
- Be specific about what to change AND what to preserve
- Include base description for better context
- Use appropriate size for the edit type
- Implement retry logic for production applications
- Test edit prompts iteratively for best results
- Consider creating variations to explore options
- Base64 images need to be decoded before saving
