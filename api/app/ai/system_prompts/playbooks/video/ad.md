# Video ad / promo clip
## Required facts
- product: what is advertised, with the one benefit to show (a bakery's fresh non, a delivery service's speed, a course's result) | ask: What is advertised, and what is the one benefit to show? | default: [mahsulot] from the user's text; the benefit shown as one visible action
- platform: where it will run (Instagram Reels/Stories 9:16, Telegram 1:1 or 16:9, YouTube pre-roll 16:9, TV screen in a shop) | ask: Where will the ad be shown? | default: Instagram Reels, vertical 9:16
- duration: clip length the tool supports (5 s, 8 s, 10 s) and total ad length if several clips | ask: How long — one 5–8 second clip or a longer ad from several clips? | default: one 8-second clip
- mood: energy and feel (warm and cozy, fast and bold, premium and slow, funny) | ask: What mood — warm, energetic, premium, funny? | default: warm, appetizing, medium pace
- brand_name: name to show or say (sign, packaging, closing text) | ask: Should the brand name appear? How exactly? | default: no readable text in the shot; the name added later in editing as [brend nomi]
- cta: the action and contact for the closing (order via Telegram, visit, call) | ask: What should the viewer do at the end? | default: closing text added in editing: [harakat] + [telefon]
## Must include
- One continuous shot: camera move + subject + action in the first sentence ("slow dolly-in on a baker pulling hot non from a tandoor, steam rising")
- The product as the hero: what it is, how it looks, the moment that shows the benefit (crispy crust breaking, a box opening, a phone tap confirming delivery)
- Setting with time of day and light ("warm tungsten bakery interior at dawn", "golden hour street in Tashkent")
- Look and grade ("cinematic, shallow depth of field, warm amber grade", "clean bright commercial look")
- Duration, pacing and format in the text ("8 seconds, medium pace, vertical 9:16"); for Veo add ambient sound and at most one short line in the stated language; for Kling/Runway note image-to-video if the user has a product photo
- Space for text: "clean area in the lower third for a caption" when the CTA is added in editing
- Negative list in prose: no readable text, no logos of other brands, no fast cuts, no extra people
## Quality rules
- One product, one benefit, one action per clip; a 15–30 s ad is described as 2–4 separate clip prompts, each self-contained, with a shared look line
- Motion realism: slow-to-medium camera and subject motion; no fast choreography, no crowds, no readable signs
- The product must appear in the first second and stay in frame; no build-up shots without it
- Use the user's real product details (color, packaging, dish name) and never invent claims, prices or discounts — the offer lives in the edited caption as [taklif]
- Faces: prefer hands, product and environment; if a person is needed, one person, simple action, no dialogue unless the tool supports audio
- Local authenticity: real objects and places named correctly (kazan, tandoor, Chorsu bazaar, a Chevrolet Cobalt taxi) instead of "Uzbek atmosphere"
- Format matches the platform: vertical 9:16 for Reels/Stories, 1:1 or 16:9 for Telegram; state it once at the end
- Length 60–120 words, one paragraph, no headings or flags
## Avoid
- A storyboard with "then… then… then…" inside one clip prompt
- Readable slogans, phone numbers or prices rendered by the video model
- Celebrity likeness, other brands' logos, copyrighted characters
- Vague "make it viral / make it professional" instead of camera, light, action and pacing
- Ignoring the tool's clip length (asking for a 30-second continuous shot)
