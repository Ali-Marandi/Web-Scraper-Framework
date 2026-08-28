import ZAI, { VisionMessage } from 'z-ai-web-dev-sdk';

async function main(imageUrl: string, prompt: string) {
	try {
		const zai = await ZAI.create();

		const messages: VisionMessage[] = [
			{
				role: 'assistant',
				content: [
					{ type: 'text', text: 'Output only text, no markdown.' }
				]
			},
			{
				role: 'user',
				content: [
					{ type: 'text', text: prompt },
					{ type: 'image_url', image_url: { url: imageUrl } }
				]
			}
		];

		const response = await zai.chat.completions.createVision({
			model: 'glm-4.6v',
			messages,
			thinking: { type: 'disabled' }
		});

		const reply = response.choices?.[0]?.message?.content;
		console.log('Image Understanding Result:');
		console.log(reply ?? JSON.stringify(response, null, 2));
	} catch (err: any) {
		console.error('Image understanding failed:', err?.message || err);
	}
}

// Example usage - analyze an image
main(
	"https://cdn.bigmodel.cn/static/logo/register.png",
	"Please analyze this image and describe what you see in detail."
);
