```mermaid
graph LR
    ROOT[ColorInfo Website] --> MAIN[Main Color Categories]
    ROOT --> SHADE[Color Shades Pages]
    ROOT --> SYM[Symbolism Pages]
    ROOT --> REL[Religious Significance]
    ROOT --> SCI[Scientific Information]
    
    subgraph "Data Extraction Targets"
        MAIN --> M1["Color Category List
                     Selector: ul.color-categories"]
        MAIN --> M2["Category Images
                     Selector: img.category-image"]
        
        SHADE --> S1["Shade Grid
                      Selector: div.shade-grid"]
        SHADE --> S2["Color Samples
                      Selector: div.color-sample"]
        SHADE --> S3["Hex Codes
                      Selector: span.hex-code"]
        SHADE --> S4["Color Names
                      Selector: h3.color-name"]
        SHADE --> S5["Color Descriptions
                      Selector: p.color-description"]
        
        SYM --> SY1["Symbolism Content
                     Selector: div.symbolism-content"]
        SYM --> SY2["Cultural References
                     Selector: ul.cultural-references"]
        SYM --> SY3["Emotional Associations
                     Selector: div.emotional-assoc"]
        
        REL --> R1["Religious References
                    Selector: div.religious-significance"]
        REL --> R2["Ceremonial Uses
                    Selector: ul.ceremonial-uses"]
        REL --> R3["Spiritual Meanings
                    Selector: div.spiritual-meaning"]
        
        SCI --> SC1["Physics Properties
                     Selector: div.color-physics"]
        SCI --> SC2["Perception Data
                     Selector: div.perception-info"]
        SCI --> SC3["Pigment Information
                     Selector: div.pigment-details"]
    end
    
    subgraph "Color Data Schema"
        COLOR[Color Object] --> C1["Base Properties:
                                  - id (unique identifier)
                                  - name (string)
                                  - hex_code (string)
                                  - rgb_values (array)
                                  - hsl_values (array)
                                  - category (string)
                                  - description (text)"]
        
        COLOR --> C2["Visual Properties:
                     - brightness (number)
                     - saturation (number)
                     - temperature (warm/cool)
                     - complementary_colors (array)
                     - analogous_colors (array)"]
        
        COLOR --> C3["Cultural Context:
                     - symbolism (array of objects)
                     - cultural_significance (array)
                     - historical_usage (array)
                     - art_movements (array)"]
                     
        COLOR --> C4["Relationships:
                     - religious_connections (array)
                     - emotional_responses (array)
                     - scientific_properties (object)
                     - common_combinations (array)"]
    end
    
    subgraph "Scraping Flow"
        FLOW1["1. Crawl Main Category Pages"] --> FLOW2["2. Extract All Color Category URLs"]
        FLOW2 --> FLOW3["3. For Each Category: Scrape All Shade Pages"]
        FLOW3 --> FLOW4["4. Extract Color Data (Name, Hex, Description)"]
        FLOW4 --> FLOW5["5. Follow Related Links (Symbolism, Religion, Science)"]
        FLOW5 --> FLOW6["6. Build Relationship Graph Between Colors and Concepts"]
    end
    
    subgraph "Relationship Mapping"
        REL_MAP["Color Relationships"] --> REL1["Color → Symbolism
                                                (e.g., Red → Passion, Danger, Energy)"]
        REL_MAP --> REL2["Color → Religious Significance
                          (e.g., White → Purity in Christianity)"]
        REL_MAP --> REL3["Color → Emotional Response
                          (e.g., Blue → Calm, Trust, Serenity)"]
        REL_MAP --> REL4["Color → Scientific Property
                          (e.g., Blue → Shortest Wavelength)"]
        REL_MAP --> REL5["Color → Color Combinations
                          (e.g., Purple + Yellow = Complementary)"]
    end
    
    classDef pages fill:#f9f,stroke:#333,stroke-width:1px
    classDef structure fill:#bbf,stroke:#333,stroke-width:1px
    classDef data fill:#dfd,stroke:#333,stroke-width:1px
    classDef flow fill:#ffd,stroke:#333,stroke-width:1px
    classDef relationships fill:#fcc,stroke:#333,stroke-width:1px
    
    class MAIN,SHADE,SYM,REL,SCI pages
    class M1,M2,S1,S2,S3,S4,S5,SY1,SY2,SY3,R1,R2,R3,SC1,SC2,SC3 structure
    class COLOR,C1,C2,C3,C4 data
    class FLOW1,FLOW2,FLOW3,FLOW4,FLOW5,FLOW6 flow
    class REL_MAP,REL1,REL2,REL3,REL4,REL5 relationships
    ```