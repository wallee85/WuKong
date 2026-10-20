shader_type canvas_item;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform sampler2D paper_tex : repeat_enable, filter_linear_mipmap;

uniform float edge_threshold : hint_range(0.01, 0.6) = 0.14;
uniform float edge_strength : hint_range(0.1, 4.0) = 1.15;
uniform float desaturate : hint_range(0.0, 1.0) = 0.32;
uniform float paper_strength : hint_range(0.0, 1.0) = 0.35;
uniform vec3 ink_color : source_color = vec3(0.05, 0.06, 0.08);
uniform vec3 paper_color : source_color = vec3(0.94, 0.91, 0.83);

float luma(vec3 c) {
	return dot(c, vec3(0.299, 0.587, 0.114));
}

void fragment() {
	vec2 uv = SCREEN_UV;
	vec2 px = SCREEN_PIXEL_SIZE * 1.4;

	vec3 base = texture(screen_tex, uv).rgb;
	float centre = luma(base);
	float dx = luma(texture(screen_tex, uv + vec2(px.x, 0.0)).rgb)
			- luma(texture(screen_tex, uv - vec2(px.x, 0.0)).rgb);
	float dy = luma(texture(screen_tex, uv + vec2(0.0, px.y)).rgb)
			- luma(texture(screen_tex, uv - vec2(0.0, px.y)).rgb);
	float edge = smoothstep(edge_threshold, edge_threshold * 2.5, length(vec2(dx, dy)) * edge_strength);

	vec3 col = mix(base, vec3(centre), desaturate);
	col = mix(col, paper_color, 0.16);
	col *= mix(0.90, 1.10, smoothstep(0.15, 0.85, centre));

	float paper = texture(paper_tex, uv * vec2(5.0, 3.0)).r;
	col *= mix(1.0, paper / 0.90, paper_strength);

	col = mix(col, ink_color, edge * 0.72);
	COLOR = vec4(col, 1.0);
}

