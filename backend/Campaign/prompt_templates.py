# Campaign/prompt_templates.py

"""
Professional Image Prompt Templates Library
Organized by industry category with technical patterns extracted from high-quality advertising prompts.
These patterns provide the technical framework while allowing customization for each user's specific product.
"""

from typing import List, Dict, Any

# ============================================================================
# FOOD & BEVERAGE PHOTOGRAPHY PATTERNS
# ============================================================================

FOOD_BEVERAGE_PATTERNS = {
    "splash_product": {
        "camera_specs": "shot on full-frame DSLR, 100mm macro lens, f/2.8, ISO 100, 1/2000s, high-speed flash photography",
        "lighting_setup": "dramatic studio lighting with soft diffused key light from front-left, strong rim light from back-right defining edges and liquid contours, subtle warm backlight creating glow, controlled specular highlights",
        "composition_structure": """
Foreground: {product_container} (bottle/can/cup/glass) {positioning} (centered upright / floating mid-air / tilted diagonally), product label clearly visible and razor-sharp with brand text "{brand_name}" readable, {material_texture} (matte aluminum / glossy plastic / transparent glass) with condensation droplets covering surface
Midground: dramatic {liquid_type} (water / sauce / chocolate / milk) splash exploding {direction} (upward / around / wrapping) the {product_container} in frozen mid-air motion, {motion_description} (crown-shaped splash / arcing liquid sheets / suspended droplets / violent eruption), realistic liquid physics with sharp splash edges and glossy viscosity
Background: {background_color} (dark moody / vibrant monochrome / gradient studio) background with {background_effect} (soft vignette / volumetric light rays / circular motion blur), {depth_element} (shallow depth of field / soft bokeh)
        """,
        "material_details": "{container_material} (aluminum can / plastic bottle / glass cup) with {surface_quality} (glossy reflections / matte finish / condensation beads), {texture_details} (ribbed cap / embossed logo / printed label texture), realistic {material_property} (metallic reflections / transparent refraction / frosted glass)",
        "motion_elements": "high-speed splash photography style, {motion_subject} ({liquid_name} / ingredients / garnishes) frozen in motion, {motion_details} (droplets suspended mid-air at different depths / explosive burst from container / swirling liquid ribbons / crown-shaped splash edges), realistic gravity-defying liquid physics, micro droplets and mist particles, {additional_motion} (flying ingredients / floating ice cubes / spinning garnish leaves)",
        "additional_elements": "{complementary_items} (fresh ingredients / ice cubes / chocolate bars / fruit slices / mint leaves / coffee beans) {element_placement} (flying around product / resting at base / embedded in splash / floating at multiple depths), {element_details} (realistic textures / visible moisture / natural imperfections / sharp edges)",
        "color_palette": "{primary_colors} with {color_treatment} (high contrast / vibrant saturation / cinematic color grading / warm tones / cool blue tones), {color_mood} (appetizing / refreshing / luxurious / energetic)",
        "quality_suffix": "ultra-realistic, 8K resolution, photorealistic textures, hyper-detailed, cinematic color grading, professional commercial food advertising style, ultra-sharp focus, high dynamic range, no motion blur, premium {product_category} marketing poster aesthetic"
    },
    
    "floating_product": {
        "camera_specs": "shot on professional DSLR, 85mm lens, f/2.8, ISO 100, commercial product photography setup",
        "lighting_setup": "clean studio lighting with three-point setup - soft key light from front for even illumination, rim light from back creating edge separation, fill light reducing harsh shadows, high-key reflections for glossy surfaces",
        "composition_structure": """
Foreground: {product_type} (burger / taco / wrap / dessert) floating mid-air in {position} (centered / slightly off-center), {product_details} (stacked layers / wrapped tortilla / assembled components) with {texture_focus} (visible ingredients / charred marks / seasoning / sauce drips)
Midground: {ingredients} (lettuce / tomatoes / cheese / meat / sauce / toppings) frozen in motion {motion_pattern} (exploding outward / suspended around / falling naturally), ingredients at varying depths showing {ingredient_details} (diced vegetables / melted cheese / crispy texture / fresh herbs / lime wedges)
Background: {background_style} (vibrant monochromatic / clean gradient / textured studio backdrop) in {color_scheme} colors, {background_treatment} (no props / minimal surface / clean negative space)
        """,
        "material_details": "{food_textures} (crispy breading / charred grill marks / melted cheese / toasted bread / glossy sauce), visible {detail_level} (moisture on vegetables / oil sheen / seasoning granules / bread texture / meat fibers)",
        "motion_elements": "high-speed food photography with {motion_freeze} (ingredients exploding / components suspended / sauce splashing / crumbs flying), {motion_specifics} (cilantro leaves spinning / tomato cubes tossed / onion bits scattered / lime wedges halved mid-air / droplets frozen), realistic motion physics without blur",
        "additional_elements": "{garnish_elements} (fresh herbs / citrus slices / vegetable pieces / spices) {placement} (floating around / scattered below / integrated in composition), {surface_element} (parchment paper / wooden board / clean surface / sauce pooling)",
        "color_palette": "{food_colors} (vivid natural / appetizing warm tones / fresh vibrant), {color_treatment} (high contrast / saturated / natural color grading), {mood_colors} for {emotion} (appetizing / fresh / energetic) feel",
        "quality_suffix": "ultra-realistic, 8K resolution, hyper-detailed textures, photorealistic, dramatic commercial food photography, macro food detail, glossy textures, sharp focus, premium fast-food commercial aesthetic, cinematic advertising style"
    },
    
    "product_hero_shot": {
        "camera_specs": "shot on full-frame DSLR, 50mm lens, f/4, ISO 100, studio product photography, straight-on hero shot perspective",
        "lighting_setup": "bright clean studio lighting, high-key illumination with soft diffused light, crisp shadows for depth, balanced highlights preventing overexposure, professional commercial lighting setup",
        "composition_structure": """
Foreground: {product_container} (can / bottle / jar / package) {positioning} (centered upright / straight-on view / slightly angled), {label_details} (brand name "{brand_name}" clearly readable / product type text visible / logo sharp and aligned), {container_specs} (tall slim can / transparent bottle / glass jar / matte packaging)
Midground: {dynamic_element} (water splash / liquid explosion / ingredient burst) {motion_type} (exploding symmetrically / wrapping around / erupting from top) with {motion_quality} (frozen droplets / dynamic arcs / suspended particles)
Background: {background_type} (vibrant monochromatic / two-tone split / clean gradient) in {brand_colors} colors, {background_details} (vertical panel accent / textured surface / smooth gradient), {depth} (shallow depth of field / soft background blur)
        """,
        "material_details": "{container_material} (aluminum can / glass bottle / plastic jar) with {surface_treatment} (glossy reflections / matte finish / condensation droplets / label texture), {branding_quality} (sharp typography / accurate print texture / embossed elements / color-accurate logo)",
        "motion_elements": "{splash_type} (water splash / liquid explosion / cream eruption) {splash_details} (forming symmetrical crown / arcing outward / frozen mid-burst), {droplet_physics} (suspended droplets of varying sizes / motion arcs / micro-spray particles), realistic surface tension and refraction",
        "additional_elements": "{product_ingredients} (fresh fruit slices / whole ingredients / natural elements / garnishes) {element_placement} (arranged at base / floating in splash / resting naturally on surface), {surface_type} (wooden tabletop / reflective surface / textured background / clean platform)",
        "color_palette": "{primary_brand_colors} with {secondary_accent}, {color_intensity} (vibrant / bold / fresh / clean), {color_grading} (bright high-key / saturated / natural)",
        "quality_suffix": "ultra-realistic, 8K resolution, photorealistic, ultra-sharp detail, vivid natural colors, premium juice advertising style, modern FMCG product aesthetic, professional commercial beverage photography, high dynamic range, no people, no clutter"
    }
}

# ============================================================================
# BEAUTY & SKINCARE PHOTOGRAPHY PATTERNS
# ============================================================================

BEAUTY_SKINCARE_PATTERNS = {
    "water_splash_product": {
        "camera_specs": "shot on professional DSLR, 100mm macro lens, f/4, ISO 100, high-speed flash freezing motion, macro commercial product photography",
        "lighting_setup": "dramatic high-speed flash lighting setup - strong side rim light defining water contours and edges, soft frontal key light for product label clarity, gentle backlight glow creating luminosity, controlled specular highlights on wet surfaces",
        "composition_structure": """
Foreground: {product_type} (squeeze tube / pump bottle / jar / container) {positioning} (standing upright centered / angled diagonally / floating mid-air) on {platform} (round pedestal / stone surface / reflective base), {product_details} (brand name "{brand_name}" vertical typography / label text sharp and readable / {material} finish with {color} accents)
Midground: crystal-clear {liquid_type} (water / cream / lotion) violently splashing {splash_direction} (upward and outward / wrapping around / erupting behind) the {product_type}, {splash_characteristics} (forming arched liquid sheets / crown-shaped splash edges / suspended droplets and micro-spray / realistic refraction and glass-like highlights)
Background: {background_color} (monochromatic soft / gradient studio / pastel) background with {background_treatment} (smooth gradient / soft vignette / clean minimal), {surface_treatment} (reflective wet surface showing mirror reflections / matte platform)
        """,
        "material_details": "{packaging_material} (white matte squeeze tube / glossy plastic bottle / frosted glass jar) with {surface_details} (ribbed crimp / cylindrical cap / pump dispenser), {texture_quality} (soft-touch plastic / subtle highlights / fine texture), {label_specs} (sharp readable text / color-accurate printing / embossed elements)",
        "motion_elements": "high-speed splash photography with motion frozen, {liquid_motion} (water violently splashing / cream erupting / lotion bursting) with {motion_details} (arched liquid sheets / crown-shaped edges / suspended droplets at multiple depths / micro-spray particles), realistic liquid physics showing {physics_details} (surface tension / refraction through droplets / glass-like highlights / realistic viscosity)",
        "additional_elements": "{natural_elements} (fresh mint leaves / botanical ingredients / flower petals / natural materials) {element_state} (bursting through splash / floating mid-air / partially submerged / wet and glossy), {element_details} (visible leaf veins / serrated edges / natural textures / water droplets clinging to surfaces)",
        "color_palette": "{brand_color_scheme} (soft pastels / clinical white-green / natural earth tones) with {color_mood} (fresh / clean / premium / natural), {color_treatment} (high-key / balanced / soft saturation)",
        "quality_suffix": "premium clinical skincare advertising aesthetic, hyper-detailed liquid physics, photorealistic textures, ultra-sharp focus, high dynamic range, 8K resolution, no people, no motion blur, no extra props, macro beauty commercial style"
    },
    
    "natural_environment_product": {
        "camera_specs": "shot on professional camera, 85mm lens, f/2.8, ISO 100, natural light photography with studio enhancement",
        "lighting_setup": "natural diffused daylight with studio augmentation - soft key light from front, gentle rim light separating subject from background, warm color temperature creating inviting mood, balanced highlights and soft shadows",
        "composition_structure": """
Foreground: {product_container} (tube / bottle / jar) {positioning} (standing upright centered / angled naturally) in {environment} (lush field / natural setting / botanical garden), {product_specs} (brand "{brand_name}" label fully visible and sharp / {material_type} packaging / {color_scheme} design elements)
Midground: {natural_setting} (strawberry field / flower garden / herb plants / natural landscape) with {setting_details} (vibrant green grass and leaves / rows of plants / natural vegetation), {depth_elements} (some elements sharp in mid-plane / others blurred for depth)
Background: {background_environment} (soft bokeh background / blurred natural landscape / out-of-focus foliage) fading into {background_treatment} (creamy blur / soft atmospheric depth / pastel sky)
        """,
        "material_details": "{packaging_type} (soft matte tube / glossy bottle / textured jar) with {packaging_details} (fine ribbed crimp / cylindrical cap / embossed logo), {surface_quality} (clean with subtle reflections / no fingerprints / realistic material texture)",
        "motion_elements": "{floating_elements} (whole fruits / flower petals / botanical ingredients / natural items) {motion_pattern} (floating and falling gently / suspended at different depths / drifting naturally through air), {depth_distribution} (some sharp in foreground / others blurred in background emphasizing depth)",
        "additional_elements": "{environmental_details} (tiny dew droplets on grass / natural moisture on ingredients / organic textures), {ground_elements} (natural grass forming ground plane / leaves and vegetation / scattered ingredients)",
        "color_palette": "{natural_colors} (vibrant greens / warm earth tones / fresh organic colors) with {color_grading} (cinematic nature-inspired / warm natural light / soft saturation), {mood_palette} creating {desired_mood} (fresh / organic / premium natural) aesthetic",
        "quality_suffix": "premium clean-beauty advertising aesthetic, ultra-sharp product focus, photorealistic natural textures, high dynamic range, 8K resolution, no people, no extra props, no motion blur, macro-level clarity, professional natural cosmetic photography"
    },
    
    "cream_explosion_product": {
        "camera_specs": "shot on full-frame DSLR, 100mm macro lens, f/2.8, ISO 100, high-speed photography setup",
        "lighting_setup": "soft diffused studio lighting with controlled shadows - gentle key light from front creating even illumination, rim light for edge definition, fill light reducing harsh shadows, crisp reflections on packaging",
        "composition_structure": """
Foreground: {product_type} (tube / jar / bottle) {positioning} (angled diagonally / floating mid-air / tilted dynamically), {branding_details} (brand name "{brand_name}" clearly readable / {logo_colors} logo visible / product name sharp), {packaging_material} ({material_type} with {texture_finish})
Midground: rich creamy {product_substance} (lotion / cream / gel) splash {splash_behavior} (erupting behind tube / exploding outward / frozen in dramatic motion), {splash_details} (smooth glossy viscosity / thick folds and curved sheets / realistic cream texture / frozen motion arcs)
Background: clean minimal {background_color} studio background with {background_elements} (oversized typography partially visible / editorial layout / smooth gradient), {depth_treatment} (shallow depth of field / soft focus background)
        """,
        "material_details": "{tube_material} (matte white squeeze tube / glossy plastic bottle / premium glass jar) with {detail_specs} (soft-touch plastic / subtle highlights / {accent_color} logo / {secondary_color} emblem), {texture_realism} (realistic material properties / accurate reflections / fine surface details)",
        "motion_elements": "{cream_motion} (cream splash erupting / lotion bursting / gel exploding) with {motion_characteristics} (smooth glossy viscosity / thick elastic folds / curved splash sheets frozen in motion / realistic cream physics)",
        "additional_elements": "{ingredient_elements} (whole almonds / coconut halves / botanical ingredients / natural components) {element_behavior} (flying outward from splash / placed strategically below / suspended at varying depths), {ingredient_details} (sharp natural textures / fibrous husks / creamy interiors / realistic organic materials)",
        "color_palette": "{color_scheme} (clean whites and pastels / warm beiges and golds / natural earth tones) with {accent_colors}, {color_mood} (luxury / premium / natural / clean) aesthetic",
        "quality_suffix": "luxury FMCG skincare aesthetic, perfectly balanced composition, ultra-sharp textures, photorealistic materials, high dynamic range, 8K resolution, no people, no motion blur, professional global brand advertising style, premium beauty commercial photography"
    },
    
    "lifestyle_model_product": {
        "camera_specs": "shot on professional camera, 85mm portrait lens, f/2.8, ISO 200, natural light augmented with studio fill",
        "lighting_setup": "natural diffused daylight filtering through environment, soft highlights on skin, gentle rim light separating subject from background, warm natural color temperature, balanced exposure for skin tones and product",
        "composition_structure": """
Foreground: {model_description} (young woman / model) with {skin_details} (smooth glowing skin / {skin_tone} complexion / natural beauty), {model_styling} (wet slicked-back hair / natural makeup / serene expression / eyes gently closed), {water_details} (water droplets visible on face, shoulders, and skin / skin subtly reflecting soft light)
Midground: {model_action} (holding {product_type} / presenting product naturally / using product), {product_details} (transparent {container_type} filled with {product_color} liquid / brand "{brand_name}" label clearly readable / {dispenser_type} angled toward camera)
Background: {environment_setting} (lush tropical rainforest / natural spa environment / waterfall setting / botanical garden) with {environmental_details} (dense green leaves framing composition / soft-focus foliage / {background_feature} creating atmosphere), {atmospheric_elements} (mist and fine water spray / humid fresh atmosphere / natural depth)
        """,
        "material_details": "{product_container} (transparent pump bottle / glass container / premium packaging) with {label_details} (round label with {color_scheme} accents / {dispenser_color} pump / accurate branding typography)",
        "motion_elements": "{environmental_motion} (waterfall cascading / mist floating / water spray suspended), creating {atmosphere} (humid fresh environment / spa-like mood / natural refreshing setting)",
        "additional_elements": "{natural_elements} (dense tropical leaves / botanical foliage / natural vegetation) {element_placement} (framing foreground / soft focus on sides / creating natural depth), {atmospheric_details} (natural diffused light filtering / soft highlights / gentle shadows)",
        "color_palette": "{natural_color_scheme} (lush greens / natural skin tones / fresh botanical colors) with {product_accent_colors}, {color_grading} (cinematic natural look / balanced highlights / soft saturation) creating {mood} (eco-luxury / natural wellness / premium herbal) aesthetic",
        "quality_suffix": "premium herbal skincare brand aesthetic, eco-luxury feel, balanced composition, photorealistic textures, cinematic color grading, high dynamic range, ultra-detailed, 8K resolution, no motion blur, professional beauty advertising style, natural wellness photography"
    }
}

# ============================================================================
# TECH / SaaS / AI PHOTOGRAPHY PATTERNS
# ============================================================================

TECH_SAAS_PATTERNS = {
    "workspace_product": {
        "camera_specs": "shot on professional camera, 50mm lens, f/2.8, ISO 100, clean product photography setup",
        "lighting_setup": "soft studio lighting with gradient background illumination, clean modern lighting creating subtle depth shadows, balanced highlights without overexposure, professional tech product lighting",
        "composition_structure": """
Foreground: sleek {device_type} (laptop / desktop / tablet) {positioning} (placed on clean desk / angled three-quarter view / centered on surface), {device_details} ({device_brand}-style / modern minimalist design / {color} finish)
Midground: {screen_content} (displaying {interface_type} / showing {application_name} / presenting {ui_elements}), {ui_details} (headline text "{headline_text}" / clean cards and buttons / modern typography / {design_elements})
Background: smooth {color_scheme} gradient ({primary_color}-to-{secondary_color} / clean white-to-gray / modern blue-purple) with {background_treatment} (soft studio lighting / subtle depth shadows / clean minimal backdrop)
        """,
        "material_details": "{device_material} (sleek silver aluminum / matte black finish / modern glass and metal), {surface_quality} (realistic reflections / soft highlights / premium build quality / glassy screen with accurate reflections)",
        "motion_elements": "{floating_elements} (translucent UI wireframes / interface panels / glassmorphism elements) {element_behavior} (floating around device / layered in perspective / softly glowing), {element_style} (semi-transparent / modern design / futuristic aesthetic)",
        "additional_elements": "{supplementary_devices} (smartphone / tablet / second screen) {placement} (standing to right / lying flat / showing responsive view), {workspace_items} (minimal desk setup / clean surface / reflective base)",
        "color_palette": "{tech_color_scheme} (modern blues and purples / clean whites and grays / corporate professional colors) with {accent_colors}, {color_treatment} (high contrast / clean modern / professional corporate) creating {brand_mood} (innovative / professional / trustworthy) feel",
        "quality_suffix": "high-end digital design aesthetic, futuristic yet professional, sharp focus, soft reflections, realistic lighting, premium SaaS/tech branding look, ultra-detailed, crisp typography, balanced composition, 4K resolution, polished commercial graphic design style"
    },
    
    "3d_illustration_tech": {
        "camera_specs": "3D rendered scene, cinematic camera angle, studio render setup, clean digital composition",
        "lighting_setup": "studio lighting with smooth shadows, glossy material highlights, controlled speculars on reflective surfaces, soft global illumination, modern tech aesthetic lighting",
        "composition_structure": """
Foreground: {main_device} (laptop / computer / device) {positioning} (on clean surface / centered in frame / angled naturally), {screen_details} (displaying {content_type} / showing {interface_elements} / presenting {visual_data})
Midground: {3d_elements} (rocket launching / robotic arms / mechanical components / floating objects) {element_behavior} (extending from device / launching outward / connected by glowing lines / symbolizing {concept})
Background: soft gradient in {color_palette} ({color_range} tones / muted {color_family} / modern {color_style}), {background_details} (clean studio backdrop / smooth lighting / subtle depth)
        """,
        "material_details": "{material_types} (metallic textures / glossy surfaces / matte finishes), {detail_quality} (detailed fins and components / realistic material properties / accurate reflections / smooth 3D render quality)",
        "motion_elements": "{dynamic_elements} (floating digital icons / glowing particles / UI symbols / data visualization) {motion_quality} (suspended around scene / orbiting / connected by light trails)",
        "additional_elements": "{foreground_objects} (geometric blocks / spheres / symbolic elements) {object_placement} (stacked in foreground / arranged for balance / creating depth), {object_meaning} (symbolizing {concept} / representing {idea})",
        "color_palette": "{primary_colors} with {secondary_accents}, {color_mood} (vibrant / playful / professional / modern), {color_treatment} (high contrast / bold saturated / clean gradients)",
        "quality_suffix": "ultra-detailed, clean 3D render, playful yet professional aesthetic, sharp focus, high contrast, vibrant colors, premium tech illustration style, 4K resolution, commercial-quality digital artwork, modern SaaS marketing visual"
    },
    
    "minimalist_design_poster": {
        "camera_specs": "flat design composition, editorial layout perspective, print-ready graphic design setup",
        "lighting_setup": "soft studio lighting creating subtle shadows, clean professional illumination, Swiss-style editorial lighting, minimal shadow depth for clean aesthetic",
        "composition_structure": """
Foreground: clean {background_color} textured background overlaid by {design_elements} (faint grid lines / circular guides / technical drafting elements), {main_text} (bold modern typography reading "{headline_text}" / {emphasis_treatment} on key words)
Midground: {physical_objects} (realistic stopwatch / metallic pens / precision tools) {object_placement} (partially cropped in corners / placed diagonally / creating visual interest), {object_details} (photorealistic rendering / soft reflections / metallic textures)
Background: {background_treatment} (clean white / light textured / subtle gradient), {layout_style} (Swiss-style / editorial design / perfect spacing and alignment)
        """,
        "material_details": "{object_materials} (silver metallic / realistic metal finishes / glass elements), {texture_quality} (realistic reflections / soft highlights / accurate material properties / detailed surface textures)",
        "motion_elements": "static composition with {dynamic_elements} (diagonal placement / layered depth / strategic positioning) creating {visual_flow} (movement through composition / eye guidance / balanced energy)",
        "additional_elements": "{branding_elements} (profile section / contact details / social handles / pagination dots), {text_elements} (supporting paragraph / call-to-action / descriptive copy) {text_treatment} (clean modern font / perfect hierarchy / minimal style)",
        "color_palette": "{neutral_base} (calm whites / light grays / clean backgrounds) with {accent_color} ({brand_color} highlights / strategic color use / minimal palette), {color_philosophy} creating {design_mood} (professional / precise / conversion-focused) aesthetic",
        "quality_suffix": "soft studio lighting, subtle shadows, Swiss-style layout, editorial design aesthetic, perfect spacing and alignment, premium print-ready look, ultra-sharp typography, realistic metallic textures, professional designer portfolio poster, ultra-detailed, high-resolution, 4K quality, modern UX/UI branding aesthetic"
    },
    
    "product_showcase_tech": {
        "camera_specs": "shot on professional camera, 35mm lens, f/2.8, ISO 100, product photography with lifestyle context",
        "lighting_setup": "soft studio lighting with gradient background, clean modern illumination, realistic shadows for depth, professional commercial lighting creating premium tech aesthetic",
        "composition_structure": """
Foreground: {primary_text} (bold {color} typography / modern sans-serif font / strong hierarchy) {text_content} (reading "{main_headline}" / followed by subtext "{supporting_text}")
Midground: sleek {device_type} (laptop / monitor / device) {positioning} (placed at three-quarter angle / on reflective surface / showing {screen_content}), {screen_details} (displaying {ui_type} / modern {theme} theme / {design_elements})
Background: minimalist {background_color} gradient ({color_range} / clean white-to-gray / professional tone) with {lighting_treatment} (soft studio lighting / clean backdrop)
        """,
        "material_details": "{device_finish} (dark-gray / sleek aluminum / modern premium), {surface_quality} (realistic shadows / sharp focus / glassy screen reflections / photorealistic 3D render quality)",
        "motion_elements": "static professional composition with {design_elements} (feature cards / bullet points with icons / call-to-action buttons) {element_treatment} (clean modern design / perfect alignment / professional hierarchy)",
        "additional_elements": "{footer_section} (branding / contact details / website / phone numbers), {graphic_elements} (icons / badges / visual markers) {styling} (clean modern / minimal professional)",
        "color_palette": "{primary_scheme} (clean blacks and whites / modern grays / professional neutrals) with {brand_accent}, {contrast_level} (high contrast typography / balanced tones) creating {aesthetic} (premium agency / professional SaaS / modern corporate) feel",
        "quality_suffix": "premium SaaS/agency aesthetic, ultra-clean composition, realistic shadows, sharp focus, glassy screen reflections, professional lighting, high contrast typography, photorealistic 3D render, commercial marketing quality, ultra-detailed, 4K resolution, modern tech branding"
    }
}

# ============================================================================
# TRAVEL & HOSPITALITY PHOTOGRAPHY PATTERNS
# ============================================================================

TRAVEL_HOSPITALITY_PATTERNS = {
    "destination_poster": {
        "camera_specs": "shot on professional camera, 24mm wide-angle lens, f/8, ISO 100, landscape photography setup, vertical poster composition",
        "lighting_setup": "natural golden-hour lighting with warm color temperature, cinematic color grading, bright natural illumination creating vibrant atmosphere, balanced highlights and rich shadows",
        "composition_structure": """
Foreground: {foreground_subject} (tourist seen from behind / traveler in scene / person in landscape) {subject_details} (wearing {clothing_description} / in {pose_description} / standing in {location_detail}), {foreground_elements} (shallow water / scenic ground / natural setting)
Midground: {main_attraction} (iconic landmark / natural wonder / cultural site / wildlife element) with {attraction_details} (realistic textures / wet reflections / natural movement / architectural detail)
Background: {background_feature} (temple on hilltop / mountain range / cityscape / natural landscape) with {background_details} (intricate architecture / colorful elements / lush greenery / atmospheric depth), Sky: {sky_description} (clear blue with soft clouds / golden sunset / dramatic atmosphere) with {sky_elements} (flying birds / hot air balloon / airplanes / natural elements)
        """,
        "material_details": "{texture_focus} (realistic skin textures / architectural details / natural materials / fabric details), {detail_level} (wet reflections / stone carvings / vegetation / atmospheric elements)",
        "motion_elements": "{dynamic_elements} (birds flying / people in motion / natural movement / atmospheric elements) {motion_treatment} (captured naturally / adding life to scene / creating depth)",
        "additional_elements": "{framing_elements} (palm leaves / natural framing / architectural elements) {element_placement} (framing corners / creating depth / adding tropical feel), {compositional_aids} (foreground interest / midground focus / background context)",
        "color_palette": "{destination_colors} (vibrant greens and golds / turquoise blues / warm earth tones / cultural color schemes), {color_treatment} (bright cinematic grading / high contrast / rich saturation / premium tourism aesthetic)",
        "quality_suffix": "professional travel advertisement look, sharp focus, realistic lighting, high contrast, premium tourism marketing aesthetic, extremely detailed, photorealistic, 8K quality, vertical poster composition, magazine-quality finish"
    },
    
    "surreal_travel_illustration": {
        "camera_specs": "3D illustration render, cinematic composition, editorial poster perspective, whimsical creative setup",
        "lighting_setup": "bright studio lighting with soft shadows, vibrant yet balanced illumination, global lighting creating optimistic feel, clean professional light for illustration style",
        "composition_structure": """
Foreground: {creative_element} (open suitcase / floating globe / miniature world) {element_details} (with detailed stitching / realistic textures / emerging landmarks), {interactive_subject} (cheerful traveler / tourist character) {subject_details} (wearing {outfit_description} / holding {travel_items} / expressing {emotion})
Midground: {landmark_collection} (famous global landmarks / iconic monuments / cultural symbols) {arrangement} (arranged in curved skyline / surrounding miniature world / emerging from {source}), {landmark_details} (Taj Mahal / Eiffel Tower / Statue of Liberty / pyramids) with {detail_quality} (accurate architectural details / realistic materials / proper scale)
Background: clean {sky_color} sky with {sky_elements} (soft fluffy clouds / colorful hot air balloons / flying airplane / floating elements) creating {atmosphere} (airy optimistic feel / travel energy / wanderlust mood)
        """,
        "material_details": "{object_textures} (leather suitcase / marble monuments / bronze statues / stone architecture), {texture_quality} (detailed stitching / architectural accuracy / realistic material properties)",
        "motion_elements": "{floating_elements} (hot air balloons / airplane / birds / travel documents) {motion_style} (floating at different depths / creating atmosphere / adding whimsy)",
        "additional_elements": "{travel_symbols} (boarding passes / passport / luggage / camera / cultural icons) {placement} (partially visible / integrated naturally / adding context), {vegetation} (lush trees / palm trees / natural greenery) {vegetation_role} (surrounding landmarks / adding life / creating miniature world)",
        "color_palette": "{vibrant_colors} (rich saturated / playful yet polished / clean bright tones), {color_balance} (balanced highlights and shadows / optimistic palette) creating {mood} (whimsical travel fantasy / inspirational wanderlust / premium adventure) aesthetic",
        "quality_suffix": "hyper-detailed photorealistic composite, whimsical surreal travel concept, premium advertising aesthetic, sharp focus, realistic textures, cinematic depth, 8K resolution, high contrast, clean and polished composition, professional travel illustration"
    },
    
    "hotel_amenities_showcase": {
        "camera_specs": "shot on professional camera, 35mm lens, f/2.8, ISO 400, hospitality interior photography",
        "lighting_setup": "warm hotel-grade illumination with soft shadows, inviting ambient lighting, balanced interior lighting with warm color temperature, professional hospitality photography lighting",
        "composition_structure": """
Foreground: clean sharp photograph of {room_type} (modern hotel bedroom / luxury suite / hospitality space), {room_details} (king-size bed with crisp white linens / plush pillows / {headboard_description} / symmetrical bedside elements)
Midground: {lighting_features} (integrated LED strip lighting / bedside wall lamps / modern fixtures) emitting {light_quality} (soft golden light / warm glow / ambient illumination), {decor_elements} (minimal modern decor / premium furnishings / thoughtful styling)
Background: {background_treatment} (warm softly blurred hotel interior / neutral beige and brown tones / cozy premium ambiance)
        """,
        "material_details": "{furniture_materials} (dark wooden headboard / crisp white linens / premium fabrics / modern fixtures), {texture_focus} (soft bedding / wood grain / metal accents / glass elements)",
        "motion_elements": "static professional composition showcasing {feature_focus} (room ambiance / lighting design / premium amenities / thoughtful details)",
        "additional_elements": "{service_icons} (minimalist circular icons / amenity symbols / service indicators) {icon_details} (evenly spaced / with labels beneath / clean design), {branding_elements} (logo badge / typography / contact information / location details) {branding_placement} (top section / footer / strategic positioning)",
        "color_palette": "{hospitality_colors} (warm beiges and browns / neutral premium tones / inviting warm palette), {color_treatment} (soft warm grading / cozy atmosphere / luxury hotel aesthetic)",
        "quality_suffix": "luxury hospitality branding, modern clean layout, professional graphic design, balanced spacing, premium marketing aesthetic, ultra-sharp details, photorealistic imagery, 8K resolution, warm inviting tone, professional hotel advertising"
    },
    
    "scenic_destination_moment": {
        "camera_specs": "shot on professional camera, 24-70mm lens, f/4, ISO 100, landscape photography with dramatic composition",
        "lighting_setup": "golden-hour sunset lighting with dramatic color temperature, cinematic natural light creating pastel sky gradients, HDR processing for rich detail in highlights and shadows",
        "composition_structure": """
Foreground: {lush_landscape} (tropical foliage / natural terrain / scenic ground level) with {foreground_details} (dense green vegetation / moss-covered rocks / natural pool / stone pathways), {human_element} (woman in {clothing_color} / traveler / tourist) {action} (swinging on jungle swing / walking path / interacting with environment)
Midground: {iconic_structure} (traditional temple / cultural monument / architectural landmark) with {structure_details} (multi-tiered pagoda / thatched roof hut / stone statues / cultural elements), {additional_subjects} (second person / complementary elements) {creating} (depth and storytelling / layered narrative)
Background: {dramatic_landscape} (misty mountains / scenic vista / atmospheric depth) with {sky_treatment} (dramatic pastel sky / pink-purple-orange gradients / golden-hour atmosphere)
        """,
        "material_details": "{natural_textures} (stone architecture / thatched roofing / wooden structures / organic materials), {texture_detail} (moss coverage / stone carving / natural weathering / authentic cultural details)",
        "motion_elements": "{captured_motion} (swinging motion / walking movement / natural activity) {motion_treatment} (dynamic capture / frozen action / storytelling movement)",
        "additional_elements": "{atmospheric_elements} (offerings / decorative elements / cultural artifacts / natural integration), {depth_creators} (layered architecture / multiple subjects / foreground-to-background flow)",
        "color_palette": "{sunset_colors} (dramatic pastels / pink-purple-orange gradients / golden hour tones), {color_saturation} (rich saturation / HDR processing / cinematic treatment) creating {emotional_tone} (dreamy yet realistic / professional travel marketing / wanderlust-inspiring) mood",
        "quality_suffix": "ultra-high-quality cinematic travel poster, dramatic lighting, sharp focus, HDR, ultra-detailed textures, professional travel marketing aesthetic, dreamy yet realistic mood, vertical poster composition, 4K resolution, magazine-quality finish, premium destination photography"
    },
    
    "world_landmarks_montage": {
        "camera_specs": "digital illustration composite, editorial poster perspective, graphic design composition",
        "lighting_setup": "bright blue sky illumination, perfect lighting balance for landmark visibility, playful yet professional lighting creating energetic atmosphere",
        "composition_structure": """
Foreground: {creative_base} (small island / central platform / miniature world) surrounded by {water_element} (turquoise ocean / reflective water / scenic base)
Midground: {landmark_arrangement} (iconic world landmarks / famous monuments / cultural symbols) {arrangement_pattern} (arranged in dynamic circular layout / emerging from island / positioned strategically), {landmark_list} (Statue of Liberty / Eiffel Tower / Big Ben / Leaning Tower of Pisa / Colosseum / Sydney Opera House / architectural silhouettes) with {detail_level} (detailed textures / accurate architecture / recognizable features)
Background: bright blue sky with {sky_elements} (fluffy white clouds / flying airplanes / floating flags / travel icons / hot air elements) {element_purpose} (symbolizing travel and motion / creating atmosphere / adding energy)
        """,
        "material_details": "{monument_materials} (teal-green patina / stone textures / metallic finishes / architectural accuracy), {detail_quality} (semi-realistic / painterly textures / sharp details / polished illustration)",
        "motion_elements": "{moving_elements} (airplanes flying / boats in water / flags waving) {motion_style} (suggesting travel / creating energy / adding dynamism)",
        "additional_elements": "{water_vessels} (small boats / yachts / maritime elements) {placement} (in water around island / adding scale / creating context), {decorative_icons} (circular travel symbols / country flags / cultural markers) {distribution} (dispersed throughout sky / adding visual interest)",
        "color_palette": "{vibrant_scheme} (rich saturated colors / bright blues and greens / warm monument tones / playful yet polished palette), {illustration_style} (clean composition / high contrast / balanced lighting) creating {aesthetic} (whimsical travel fantasy / professional poster design / visually energetic and inspirational) feel",
        "quality_suffix": "high-quality vibrant travel illustration, playful yet polished style, semi-realistic with painterly textures, sharp details, perfect lighting balance, commercial poster design, ultra-detailed, crisp edges, high contrast, 4K resolution, professional travel branding aesthetic, clean composition, visually energetic"
    }
}

# ============================================================================
# BEVERAGE & FRAGRANCE PHOTOGRAPHY PATTERNS
# ============================================================================

BEVERAGE_FRAGRANCE_PATTERNS = {
    "can_explosion": {
        "camera_specs": "shot on full-frame DSLR, 100mm macro lens, f/4, ISO 100, high-speed flash photography, commercial beverage product shot",
        "lighting_setup": "dramatic studio lighting with controlled speculars - strong rim light outlining edges, soft key light from front for label clarity, warm or cool accent lights for mood, high contrast highlights and deep shadows",
        "composition_structure": """
Foreground: {can_type} (aluminum can / metallic beverage container) {branding} (with exact "{brand_name}" logo / "{product_type}" text clearly readable / accurate typography and print fidelity), {can_details} (tall slim / standard size / {color_scheme} design / metallic texture with condensation droplets)
Midground: {liquid_explosion} ({liquid_color} {beverage_type} / soda / juice) {explosion_pattern} (exploding through can / erupting from top / splashing outward), {explosion_details} (frozen mid-motion / forming dynamic arcs / suspended droplets of varying sizes)
Background: {background_color} ({color_description} gradient / dramatic moody / vibrant monochrome) with {background_treatment} (cool-warm contrast / soft vignette / atmospheric elements / smoke or mist effects)
        """,
        "material_details": "{can_material} (metallic aluminum texture / matte or glossy finish / realistic print texture), {surface_treatment} (condensation droplets / micro-scratches / fine metallic texture / accurate brand printing)",
        "motion_elements": "{splash_physics} (liquid splashing with realistic arcs / suspended droplets / motion frozen at peak moment / dynamic liquid sheets), {droplet_detail} (varying droplet sizes / realistic surface tension / glass-like refraction)",
        "additional_elements": "{ingredients} (fresh fruits / berries / botanical elements / ice cubes) {element_behavior} (flying mid-air / suspended around can / embedded in splash / scattered naturally), {ingredient_details} (whole and halved / realistic textures / natural moisture / visible details)",
        "color_palette": "{primary_color_scheme} (rich burgundy-crimson / vibrant greens / warm mochas / cool aquatics) with {accent_treatment}, {contrast_style} (high contrast / bold colors / dramatic lighting) creating {mood} (energetic / premium / refreshing / luxurious) aesthetic",
        "quality_suffix": "ultra-realistic, 8K resolution, photorealistic, hyper-detailed textures, high contrast, cinematic lighting, premium commercial beverage advertisement, macro-level sharpness, no motion blur, bold colors, professional product photography style"
    },
    
    "perfume_splash": {
        "camera_specs": "shot on professional camera, 100mm macro lens, f/2.8, ISO 100, luxury product photography with controlled studio setup",
        "lighting_setup": "cinematic studio lighting - strong rim light outlining bottle edges and water contours, soft diffused key light from front for logo clarity, gentle backlight creating luminosity, controlled specular highlights on glass and water",
        "composition_structure": """
Foreground: {bottle_shape} (rectangular clear glass / frosted glass / faceted crystal / cylindrical) perfume bottle {positioning} (centered upright / three-quarter angle / slightly tilted), {bottle_details} (with {liquid_color} {fragrance_type} liquid / thick glass base / beveled edges / {cap_type} cap)
Midground: dramatic {splash_element} (water splash / amber resin splash / liquid perfume) {splash_behavior} (exploding upward behind cap / arcing around bottle / frozen mid-motion), {splash_characteristics} (crisp translucent droplets / arcs and sheets / realistic refraction / S-curved dynamics)
Background: {background_treatment} (cool aquatic palette / dark warm brown-black / dramatic gradient / luxury depth) with {atmospheric_elements} (glowing particles / bokeh lights / soft depth / premium ambiance)
        """,
        "material_details": "{glass_quality} (clear transparent / frosted matte / faceted crystal) with {detail_specs} (sharp beveled edges / thick glass base / realistic refraction through liquid / accurate material properties), {cap_material} ({cap_finish} spray atomizer / metallic / transparent faceted cap) with {cap_details} (mirror reflections / realistic metal finish)",
        "motion_elements": "{liquid_motion} (water/perfume/resin splashing) {motion_details} (frozen at peak moment / forming dynamic curves / creating depth separation / realistic liquid physics), {droplet_physics} (suspended droplets / realistic surface tension / glass-like refraction)",
        "additional_elements": "{luxury_ingredients} (citrus slices / flowers / vanilla pods / agarwood chips / amber crystals / botanical elements) {placement} (floating at varying depths / partially submerged / arranged naturally / creating foreground-midground-background separation), {ingredient_quality} (realistic textures / natural imperfections / moisture details)",
        "color_palette": "{fragrance_colors} (cool teal-blue aquatic / warm amber-gold / deep cobalt-navy / elegant neutrals) with {accent_colors}, {lighting_treatment} (high contrast reflections / balanced highlights / dramatic shadows) creating {luxury_mood} (premium / sophisticated / elegant / Middle-Eastern luxury / European refinement) aesthetic",
        "quality_suffix": "ultra-realistic luxury fragrance photography, editorial perfume campaign style, hyper-detailed textures, photorealistic, 8K resolution, high contrast, no blur, no distortion, premium brand advertisement aesthetic, macro-sharp focus, cinematic composition, professional beauty photography"
    },
    
    "honey_artisan": {
        "camera_specs": "shot on professional camera, 85mm lens, f/1.8, ISO 100, natural light product photography with studio enhancement",
        "lighting_setup": "natural golden-hour sunlight from back-left creating rim light, warm highlights on honey and glass, soft shadows for depth, warm color temperature, cinematic natural-light aesthetic",
        "composition_structure": """
Foreground: {jar_shape} (hexagonal glass jar / round artisan jar / premium container) filled with {honey_description} (rich amber honey / golden viscous liquid), {jar_details} ({lid_type} metal lid / realistic light refraction through glass / thick glass walls)
Midground: {honey_action} (honey dripping over rim / flowing from dipper / suspended honeycomb above / natural pouring motion), {viscosity_details} (thick viscous texture / glossy highlights / realistic honey flow / natural golden color)
Background: {setting_type} (outdoor wildflower meadow / rustic wooden table / natural organic setting) with {background_details} (rolling hills / colorful flowers / natural depth / soft bokeh blur)
        """,
        "material_details": "{jar_material} (thick glass / hexagonal shape / realistic refraction), {label_details} (cream paper label / premium typography / {brand_name} readable / textured emboss feel / perfectly aligned), {lid_quality} (gold metal / silver latch / realistic metallic finish)",
        "motion_elements": " {natural_motion} (honey dripping / dipper lifting / bees hovering / natural organic movement) {motion_treatment} (captured naturally / realistic viscosity / frozen at perfect moment)",
        "additional_elements": "{natural_elements} (honeybee on lid / honeycomb piece / chamomile flowers / wooden honey dipper / wildflowers) {element_placement} (perched naturally / resting nearby / surrounding jar / in meadow setting), {element_details} (realistic bee with wing detail / flower textures / wood grain / natural organic details)",
        "color_palette": "{honey_colors} (warm amber-gold / natural honey tones / rich golden hues) with {natural_accents} (green meadow / white flowers / earth tones), {lighting_mood} (warm natural / golden hour / inviting organic) creating {brand_aesthetic} (premium artisanal / natural authentic / luxury organic) feel",
        "quality_suffix": "ultra-realistic premium food product photography, natural daylight aesthetic, hyper-detailed textures, photorealistic, cinematic natural lighting, 8K quality, ultra-sharp details, no distortion, no blur, artisanal honey campaign style, warm inviting composition, professional organic branding"
    }
}

# ============================================================================
# PATTERN SELECTION HELPER FUNCTION
# ============================================================================

def get_pattern_by_category(visual_category: str) -> Dict[str, Any]:
    """
    Returns the appropriate pattern based on visual_category string.
    
    Args:
        visual_category: The full category string (e.g., 'food_splash_product', 'beauty_water_splash_product')
    
    Returns:
        Dictionary containing the pattern structure
    """
    
    # Map full category names to (pattern_library, subcategory)
    category_mapping = {
        # Food/Beverage
        "food_splash_product": (FOOD_BEVERAGE_PATTERNS, "splash_product"),
        "food_floating_product": (FOOD_BEVERAGE_PATTERNS, "floating_product"),
        "food_product_hero_shot": (FOOD_BEVERAGE_PATTERNS, "product_hero_shot"),
        
        # Beauty/Skincare
        "beauty_water_splash_product": (BEAUTY_SKINCARE_PATTERNS, "water_splash_product"),
        "beauty_natural_environment_product": (BEAUTY_SKINCARE_PATTERNS, "natural_environment_product"),
        "beauty_cream_explosion_product": (BEAUTY_SKINCARE_PATTERNS, "cream_explosion_product"),
        "beauty_lifestyle_model_product": (BEAUTY_SKINCARE_PATTERNS, "lifestyle_model_product"),
        
        # Tech/SaaS
        "tech_workspace_product": (TECH_SAAS_PATTERNS, "workspace_product"),
        "tech_3d_illustration_tech": (TECH_SAAS_PATTERNS, "3d_illustration_tech"),
        "tech_minimalist_design_poster": (TECH_SAAS_PATTERNS, "minimalist_design_poster"),
        "tech_product_showcase_tech": (TECH_SAAS_PATTERNS, "product_showcase_tech"),
        
        # Travel/Hospitality
        "travel_destination_poster": (TRAVEL_HOSPITALITY_PATTERNS, "destination_poster"),
        "travel_surreal_travel_illustration": (TRAVEL_HOSPITALITY_PATTERNS, "surreal_travel_illustration"),
        "travel_hotel_amenities_showcase": (TRAVEL_HOSPITALITY_PATTERNS, "hotel_amenities_showcase"),
        "travel_scenic_destination_moment": (TRAVEL_HOSPITALITY_PATTERNS, "scenic_destination_moment"),
        "travel_world_landmarks_montage": (TRAVEL_HOSPITALITY_PATTERNS, "world_landmarks_montage"),
        
        # Beverage/Fragrance/Premium
        "beverage_can_explosion": (BEVERAGE_FRAGRANCE_PATTERNS, "can_explosion"),
        "beverage_perfume_splash": (BEVERAGE_FRAGRANCE_PATTERNS, "perfume_splash"),
        "beverage_honey_artisan": (BEVERAGE_FRAGRANCE_PATTERNS, "honey_artisan"),
    }
    
    # Get the pattern
    if visual_category in category_mapping:
        pattern_library, subcategory = category_mapping[visual_category]
        return pattern_library[subcategory]
    else:
        # Fallback to default
        print(f"Warning: Unknown visual_category '{visual_category}', using default food splash pattern")
        return FOOD_BEVERAGE_PATTERNS["splash_product"]

 