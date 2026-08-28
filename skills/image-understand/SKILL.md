---
name: image-understand
description: Implement specialized image understanding capabilities using the z-ai-web-dev-sdk. Use this skill when the user needs to analyze static images, extract visual information, perform OCR, detect objects, classify images, or understand visual content. Optimized for PNG, JPEG, GIF, WebP, and BMP formats.
license: MIT
---

# Image Understanding Skill

This skill provides specialized image understanding functionality using the z-ai-web-dev-sdk package, enabling AI models to analyze, describe, and extract information from static images.

## Skills Path

**Skill Location**: `{project_path}/skills/image-understand`

this skill is located at above path in your project.

**Reference Scripts**: Example test scripts are available in the `{Skill Location}/scripts/` directory for quick testing and reference. See `{Skill Location}/scripts/image-understand.ts` for a working example.

## Overview

Image Understanding focuses specifically on static image analysis, providing capabilities for:
- Image description and scene understanding
- Object detection and recognition
- OCR (Optical Character Recognition) and text extraction
- Image classification and categorization
- Visual content analysis
- Quality assessment
- Accessibility (alt text generation)

**IMPORTANT**: z-ai-web-dev-sdk MUST be used in backend code only. Never use it in client-side code.

## Prerequisites

The z-ai-web-dev-sdk package is already installed. Import it as shown in the examples below.

## CLI Usage (For Simple Tasks)

For quick image analysis tasks, you can use the z-ai CLI instead of writing code. This is ideal for simple image descriptions, testing, or automation.

### Basic Image Analysis

```bash
# Describe an image from URL
z-ai vision --prompt "What's in this image?" --image "https://example.com/photo.jpg"

# Using short options
z-ai vision -p "Describe this image" -i "https://example.com/image.png"
```

### Analyze Local Images

```bash
# Analyze a local image file
z-ai vision -p "What objects are in this photo?" -i "./photo.jpg"

# Save response to file
z-ai vision -p "Describe the scene" -i "./landscape.png" -o description.json
```

### Multiple Images Comparison

```bash
# Compare multiple images
z-ai vision \
  -p "Compare these two images and highlight the differences" \
  -i "./photo1.jpg" \
  -i "./photo2.jpg" \
  -o comparison.json

# Analyze a series of images
z-ai vision \
  --prompt "What patterns do you see across these images?" \
  --image "https://example.com/img1.jpg" \
  --image "https://example.com/img2.jpg" \
  --image "https://example.com/img3.jpg"
```

### Advanced Analysis with Thinking

```bash
# Enable chain-of-thought reasoning for complex tasks
z-ai vision \
  -p "Count all people in this image and describe what each person is doing" \
  -i "./crowd.jpg" \
  --thinking \
  -o analysis.json

# Complex object detection with reasoning
z-ai vision \
  -p "Identify all safety hazards in this workplace image" \
  -i "./workplace.jpg" \
  --thinking
```

### Streaming Output

```bash
# Stream the analysis in real-time
z-ai vision -p "Provide a detailed description" -i "./photo.jpg" --stream
```

### CLI Parameters

- `--prompt, -p <text>`: **Required** - Question or instruction about the image(s)
- `--image, -i <URL or path>`: Optional - Image URL or local file path (can be used multiple times)
- `--thinking, -t`: Optional - Enable chain-of-thought reasoning (default: disabled)
- `--output, -o <path>`: Optional - Output file path (JSON format)
- `--stream`: Optional - Stream the response in real-time

### Supported Image Formats

- PNG (.png) - Best for diagrams, screenshots, graphics with transparency
- JPEG (.jpg, .jpeg) - Best for photos and complex images
- GIF (.gif) - Supports both static and animated images
- WebP (.webp) - Modern format with good compression
- BMP (.bmp) - Uncompressed bitmap format

### When to Use CLI vs SDK

**Use CLI for:**
- Quick image analysis or descriptions
- One-off OCR tasks
- Testing image understanding capabilities
- Simple batch processing scripts
- Generating alt text for accessibility

**Use SDK for:**
- Multi-turn conversations about images
- Complex image processing pipelines
- Production applications with error handling
- Custom integration with your application logic
- Batch processing with custom business logic

## Recommended Approach

For better performance and reliability, use base64 encoding to pass images to the model instead of image URLs.

## Basic Image Understanding Implementation

### Single Image Analysis

```javascript
import ZAI from 'z-ai-web-dev-sdk';

async function analyzeImage(imageUrl, prompt) {
  const zai = await ZAI.create();

  const response = await zai.chat.completions.createVision({
    messages: [
      {
        role: 'user',
        content: [
          {
            type: 'text',
            text: prompt
          },
          {
            type: 'image_url',
            image_url: {
              url: imageUrl
            }
          }
        ]
      }
    ],
    thinking: { type: 'disabled' }
  });

  return response.choices[0]?.message?.content;
}

// Usage examples
const description = await analyzeImage(
  'https://example.com/landscape.jpg',
  'Describe this landscape in detail, including colors, lighting, and mood'
);

const objectDetection = await analyzeImage(
  'https://example.com/room.jpg',
  'List all objects visible in this room'
);
```

### Multiple Images Comparison

```javascript
import ZAI from 'z-ai-web-dev-sdk';

async function compareImages(imageUrls, question) {
  const zai = await ZAI.create();

  const content = [
    {
      type: 'text',
      text: question
    },
    ...imageUrls.map(url => ({
      type: 'image_url',
      image_url: { url }
    }))
  ];

  const response = await zai.chat.completions.createVision({
    messages: [
      {
        role: 'user',
        content: content
      }
    ],
    thinking: { type: 'disabled' }
  });

  return response.choices[0]?.message?.content;
}

// Usage
const comparison = await compareImages(
  [
    'https://example.com/before.jpg',
    'https://example.com/after.jpg'
  ],
  'What are the key differences between these before and after images?'
);
```

### Base64 Image Support (Recommended)

```javascript
import ZAI from 'z-ai-web-dev-sdk';
import fs from 'fs';
import path from 'path';

async function analyzeLocalImage(imagePath, prompt) {
  const zai = await ZAI.create();

  // Read image file and convert to base64
  const imageBuffer = fs.readFileSync(imagePath);
  const base64Image = imageBuffer.toString('base64');
  
  // Determine MIME type based on file extension
  const ext = path.extname(imagePath).toLowerCase();
  const mimeTypes = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.bmp': 'image/bmp'
  };
  const mimeType = mimeTypes[ext] || 'image/jpeg';

  const response = await zai.chat.completions.createVision({
    messages: [
      {
        role: 'user',
        content: [
          {
            type: 'text',
            text: prompt
          },
          {
            type: 'image_url',
            image_url: {
              url: `data:${mimeType};base64,${base64Image}`
            }
          }
        ]
      }
    ],
    thinking: { type: 'disabled' }
  });

  return response.choices[0]?.message?.content;
}

// Usage
const result = await analyzeLocalImage(
  './product-photo.jpg',
  'Analyze this product image for e-commerce listing'
);
```

## Advanced Use Cases

### OCR and Text Extraction

```javascript
import ZAI from 'z-ai-web-dev-sdk';

async function extractText(imageUrl, options = {}) {
  const zai = await ZAI.create();

  const prompt = options.preserveLayout 
    ? 'Extract all text from this image. Preserve the exact layout, formatting, and structure.'
    : 'Extract all visible text from this image.';

  const response = await zai.chat.completions.createVision({
    messages: [
      {
        role: 'user',
        content: [
          { type: 'text', text: prompt },
          { type: 'image_url', image_url: { url: imageUrl } }
        ]
      }
    ],
    thinking: { type: 'disabled' }
  });

  return response.choices[0]?.message?.content;
}

// Usage examples
const receiptText = await extractText(
  'https://example.com/receipt.jpg',
  { preserveLayout: true }
);

const businessCardInfo = await extractText(
  'https://example.com/business-card.jpg'
);
```

### Object Detection and Counting

```javascript
import ZAI from 'z-ai-web-dev-sdk';

async function detectObjects(imageUrl, objectType) {
  const zai = await ZAI.create();

  const prompt = objectType 
    ? `Count and locate all ${objectType} in this image. Provide their positions and describe each one.`
    : 'Detect and list all objects in this image with their approximate locations.';

  const response = await zai.chat.completions.createVision({
    messages: [
      {
        role: 'user',
        content: [
          { type: 'text', text: prompt },
          { type: 'image_url', image_url: { url: imageUrl } }
        ]
      }
    ],
    thinking: { type: 'enabled' } // Enable thinking for complex counting
  });

  return response.choices[0]?.message?.content;
}

// Usage
const peopleCount = await detectObjects(
  'https://example.com/crowd.jpg',
  'people'
);

const allObjects = await detectObjects(
  'https://example.com/room.jpg'
);
```

### Image Classification and Tagging

```javascript
import ZAI from 'z-ai-web-dev-sdk';

async function classifyAndTag(imageUrl) {
  const zai = await ZAI.create();

  const prompt = `Analyze this image and provide a comprehensive classification:
1. Primary category (e.g., nature, urban, portrait, product)
2. Subject matter (main focus of the image)
3. Style or mood (e.g., professional, casual, artistic, vintage)
4. Color palette description
5. Suggested tags (10-15 keywords, comma-separated)

Format your response as structured JSON.`;

  const response = await zai.chat.completions.createVision({
    messages: [
      {
        role: 'user',
        content: [
          { type: 'text', text: prompt },
          { type: 'image_url', image_url: { url: imageUrl } }
        ]
      }
    ],
    thinking: { type: 'disabled' }
  });

  const content = response.choices[0]?.message?.content;
  
  try {
    return JSON.parse(content);
  } catch (e) {
    return { rawResponse: content };
  }
}

// Usage
const classification = await classifyAndTag(
  'https://example.com/photo.jpg'
);
console.log('Tags:', classification.tags);
```

### Quality Assessment

```javascript
import ZAI from 'z-ai-web-dev-sdk';

async function assessImageQuality(imageUrl) {
  const zai = await ZAI.create();

  const prompt = `Assess the technical quality of this image:
1. Sharpness and focus (1-10)
2. Exposure and brightness (1-10)
3. Color balance (1-10)
4. Composition (1-10)
5. Any technical issues (blur, noise, artifacts, etc.)
6. Overall quality rating (1-10)
7. Suggestions for improvement

Provide specific feedback for each criterion.`;

  const response = await zai.chat.completions.createVision({
    messages: [
      {
        role: 'user',
        content: [
          { type: 'text', text: prompt },
          { type: 'image_url', image_url: { url: imageUrl } }
        ]
      }
    ],
    thinking: { type: 'disabled' }
  });

  return response.choices[0]?.message?.content;
}
```

### Accessibility - Alt Text Generation

```javascript
import ZAI from 'z-ai-web-dev-sdk';

async function generateAltText(imageUrl, context = '') {
  const zai = await ZAI.create();

  const prompt = context
    ? `Generate concise, descriptive alt text for this image. Context: ${context}. Focus on the most important visual elements that convey the image's purpose.`
    : 'Generate concise, descriptive alt text for this image suitable for screen readers. Focus on key visual elements.';

  const response = await zai.chat.completions.createVision({
    messages: [
      {
        role: 'user',
        content: [
          { type: 'text', text: prompt },
          { type: 'image_url', image_url: { url: imageUrl } }
        ]
      }
    ],
    thinking: { type: 'disabled' }
  });

  return response.choices[0]?.message?.content;
}

// Usage
const altText = await generateAltText(
  'https://example.com/hero-image.jpg',
  'Website hero section for a tech startup'
);
```

### Scene Understanding

```javascript
import ZAI from 'z-ai-web-dev-sdk';

async function understandScene(imageUrl) {
  const zai = await ZAI.create();

  const prompt = `Provide a comprehensive scene analysis:
1. Setting/location type (indoor/outdoor, specific place)
2. Time of day and lighting conditions
3. Weather (if applicable)
4. People present (number, activities, interactions)
5. Key objects and their arrangement
6. Overall atmosphere and mood
7. Notable details or interesting elements`;

  const response = await zai.chat.completions.createVision({
    messages: [
      {
        role: 'user',
        content: [
          { type: 'text', text: prompt },
          { type: 'image_url', image_url: { url: imageUrl } }
        ]
      }
    ],
    thinking: { type: 'disabled' }
  });

  return response.choices[0]?.message?.content;
}
```

## Batch Processing

### Process Multiple Images

```javascript
import ZAI from 'z-ai-web-dev-sdk';

class ImageBatchProcessor {
  constructor() {
    this.zai = null;
  }

  async initialize() {
    this.zai = await ZAI.create();
  }

  async processImage(imageUrl, prompt) {
    const response = await this.zai.chat.completions.createVision({
      messages: [
        {
          role: 'user',
          content: [
            { type: 'text', text: prompt },
            { type: 'image_url', image_url: { url: imageUrl } }
          ]
        }
      ],
      thinking: { type: 'disabled' }
    });

    return response.choices[0]?.message?.content;
  }

  async processBatch(imageUrls, prompt) {
    const results = [];
    
    for (const imageUrl of imageUrls) {
      try {
        const result = await this.processImage(imageUrl, prompt);
        results.push({ imageUrl, success: true, result });
      } catch (error) {
        results.push({ 
          imageUrl, 
          success: false, 
          error: error.message 
        });
      }
    }

    return results;
  }
}

// Usage
const processor = new ImageBatchProcessor();
await processor.initialize();

const images = [
  'https://example.com/img1.jpg',
  'https://example.com/img2.jpg',
  'https://example.com/img3.jpg'
];

const results = await processor.processBatch(
  images,
  'Generate a short description suitable for social media'
);
```

## Best Practices

### 1. Image Quality and Preparation
- Use high-resolution images for better analysis accuracy
- Ensure images are well-lit and properly exposed
- For OCR, ensure text is clear and readable
- Optimize file size to balance quality and performance
- Supported formats: PNG (best for text/diagrams), JPEG (best for photos), WebP, GIF, BMP

### 2. Prompt Engineering for Images
- Be specific about what information you need
- Mention the type of image (photo, diagram, screenshot, etc.)
- For complex tasks, break down into specific questions
- Use structured prompts for JSON output
- Include context when relevant

### 3. Error Handling

```javascript
async function safeImageAnalysis(imageUrl, prompt) {
  try {
    const zai = await ZAI.create();
    
    const response = await zai.chat.completions.createVision({
      messages: [
        {
          role: 'user',
          content: [
            { type: 'text', text: prompt },
            { type: 'image_url', image_url: { url: imageUrl } }
          ]
        }
      ],
      thinking: { type: 'disabled' }
    });

    return {
      success: true,
      content: response.choices[0]?.message?.content
    };
  } catch (error) {
    console.error('Image analysis error:', error);
    return {
      success: false,
      error: error.message
    };
  }
}
```

### 4. Performance Optimization
- Cache SDK instance for batch processing
- Use base64 encoding for local images
- Implement request throttling for large batches
- Consider image preprocessing (resize, compress) for large files
- Use appropriate thinking mode (disabled for simple tasks, enabled for complex reasoning)

### 5. Security Considerations
- Validate image URLs before processing
- Implement rate limiting for public APIs
- Sanitize user-provided image data
- Never expose SDK credentials in client-side code
- Implement content moderation for user-uploaded images

## Common Use Cases

1. **E-commerce Product Analysis**: Analyze product images, extract features, generate descriptions
2. **Document Processing**: Extract text from receipts, invoices, forms, business cards
3. **Content Moderation**: Detect inappropriate content, verify image compliance
4. **Quality Control**: Identify defects, assess product quality in manufacturing
5. **Accessibility**: Generate alt text for images automatically
6. **Image Cataloging**: Auto-tag and categorize image libraries
7. **Visual Search**: Understand and index images for search functionality
8. **Medical Imaging**: Preliminary analysis with appropriate disclaimers
9. **Real Estate**: Analyze property photos, extract features
10. **Social Media**: Generate captions, hashtags, and descriptions

## Integration Examples

### Express.js API Endpoint

```javascript
import express from 'express';
import ZAI from 'z-ai-web-dev-sdk';
import multer from 'multer';

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

let zaiInstance;

async function initZAI() {
  zaiInstance = await ZAI.create();
}

// Analyze image from URL
app.post('/api/analyze-image', express.json(), async (req, res) => {
  try {
    const { imageUrl, prompt } = req.body;

    if (!imageUrl || !prompt) {
      return res.status(400).json({ 
        error: 'imageUrl and prompt are required' 
      });
    }

    const response = await zaiInstance.chat.completions.createVision({
      messages: [
        {
          role: 'user',
          content: [
            { type: 'text', text: prompt },
            { type: 'image_url', image_url: { url: imageUrl } }
          ]
        }
      ],
      thinking: { type: 'disabled' }
    });

    res.json({
      success: true,
      analysis: response.choices[0]?.message?.content
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Analyze uploaded image file
app.post('/api/analyze-upload', upload.single('image'), async (req, res) => {
  try {
    const { prompt } = req.body;
    const imageFile = req.file;

    if (!imageFile || !prompt) {
      return res.status(400).json({ 
        error: 'image file and prompt are required' 
      });
    }

    // Convert to base64
    const base64Image = imageFile.buffer.toString('base64');
    const mimeType = imageFile.mimetype;

    const response = await zaiInstance.chat.completions.createVision({
      messages: [
        {
          role: 'user',
          content: [
            { type: 'text', text: prompt },
            { 
              type: 'image_url', 
              image_url: { 
                url: `data:${mimeType};base64,${base64Image}` 
              } 
            }
          ]
        }
      ],
      thinking: { type: 'disabled' }
    });

    res.json({
      success: true,
      analysis: response.choices[0]?.message?.content
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
    console.log('Image understanding API running on port 3000');
  });
});
```

### Next.js API Route

```javascript
// pages/api/image-understand.js
import ZAI from 'z-ai-web-dev-sdk';

let zaiInstance = null;

async function getZAI() {
  if (!zaiInstance) {
    zaiInstance = await ZAI.create();
  }
  return zaiInstance;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { imageUrl, prompt } = req.body;

    if (!imageUrl || !prompt) {
      return res.status(400).json({ 
        error: 'imageUrl and prompt are required' 
      });
    }

    const zai = await getZAI();

    const response = await zai.chat.completions.createVision({
      messages: [
        {
          role: 'user',
          content: [
            { type: 'text', text: prompt },
            { type: 'image_url', image_url: { url: imageUrl } }
          ]
        }
      ],
      thinking: { type: 'disabled' }
    });

    res.status(200).json({
      success: true,
      analysis: response.choices[0]?.message?.content
    });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}
```

## Troubleshooting

**Issue**: "SDK must be used in backend"
- **Solution**: Ensure z-ai-web-dev-sdk is only imported and used in server-side code, never in client/browser code

**Issue**: Image not loading or being analyzed
- **Solution**: Verify the image URL is accessible, returns correct MIME type, and is in a supported format

**Issue**: Poor OCR accuracy
- **Solution**: Ensure text is clear and readable, increase image resolution, ensure proper lighting and contrast

**Issue**: Inaccurate object detection or counting
- **Solution**: Enable thinking mode for complex counting tasks, use high-resolution images, provide specific prompts

**Issue**: Slow response times
- **Solution**: Optimize image size (resize before upload), use base64 for local images, cache SDK instance for batch processing

**Issue**: Base64 encoding fails
- **Solution**: Verify file path is correct, check file permissions, ensure MIME type matches file extension

## Remember

- Always use z-ai-web-dev-sdk in backend code only
- The SDK is already installed - import as shown in examples
- Use `image_url` content type for static images
- Base64 encoding is recommended for better performance
- Structure prompts clearly for best results
- Enable thinking mode for complex reasoning tasks (counting, detailed analysis)
- Handle errors gracefully in production
- Validate and sanitize user inputs
- Consider privacy and security when processing user images
