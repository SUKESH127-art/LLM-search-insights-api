# src/analysis/visualizer.py
import json

from analysis.clients import openai_client
from schemas import VisualizationData, BrandVisibilityScore

async def extract_visualization_data(web_analysis_text: str) -> VisualizationData:
    """
    Uses a final LLM call to extract a structured visualization package from the web analysis text.
    The LLM is prompted to be transparent about its methodology.
    """
    print("   📊 Extracting structured visualization data from web analysis...")
    print(f"   📝 Input text length: {len(web_analysis_text)} characters")
    print(f"   📝 Input text preview: {web_analysis_text[:200]}...")
    
    extraction_prompt = f"""
    Analyze the following text, which is a summary of web search results for a specific query.
    Your task is to identify the top 5 most prominent brands mentioned.

    You must perform the following steps:
    1.  **Identify Brands**: Scan the text to find all mentioned brand names.
    2.  **Count Mentions**: Tally the number of times each brand is mentioned.
    3.  **Assess Prominence**: Evaluate the prominence of each mention. Brands mentioned earlier, in headlines, or as primary recommendations are more prominent.
    4.  **Calculate Visibility Score**: Based on a combination of mention count and prominence, calculate a 'visibility_score' for each brand on a scale of 1 to 100.
    5.  **Rank Brands**: Rank the top 5 brands from 1 to 5 based on their score.
    6.  **Explain Methodology**: Briefly (1-2 sentences) explain the specific factors you used from the text to determine the scores. For example: "Scores were based on mention frequency and prominence in lists of 'best' brands."

    Your response MUST be a single, valid JSON object that strictly follows this structure:
    {{
      "top_5_brands": ["Brand A", "Brand B", ...],
      "brand_scores": [
        {{ "brand_name": "Brand A", "visibility_score": 95, "rank": 1, "mentions": 8 }},
        {{ "brand_name": "Brand B", "visibility_score": 90, "rank": 2, "mentions": 6 }},
        ...
      ],
      "methodology_explanation": "Your explanation here."
    }}

    --- WEB ANALYSIS TEXT TO ANALYZE ---
    {web_analysis_text[:10000]}
    """
    
    print("   🤖 Making OpenAI call for visualization extraction...")
    
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a highly precise data analysis and extraction engine. Your only output must be a single, valid JSON object that strictly adheres to the user's requested format. Do not include any other text or apologies."},
                {"role": "user", "content": extraction_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        print(f"   ✅ OpenAI response received: {len(response.choices[0].message.content)} characters")
        print(f"   📄 Response content: {response.choices[0].message.content}")
        
        extracted_data = json.loads(response.choices[0].message.content)
        print(f"   🔍 Parsed JSON data: {extracted_data}")
        
        # Validate the entire JSON object against our Pydantic model
        visualization_package = VisualizationData(**extracted_data)
        
        print(f"   ✅ Successfully extracted and validated visualization package.")
        print(f"   📊 Package contains {len(visualization_package.brand_scores)} brand scores")
        return visualization_package

    except Exception as e:
        print(f"   ❌ Error extracting visualization data: {e}")
        print(f"   🔍 Error type: {type(e).__name__}")
        import traceback
        print(f"   📋 Full traceback: {traceback.format_exc()}")
        
        # Check if this is due to failed web analysis
        if "Unable to perform web analysis" in web_analysis_text or "SERP API did not return" in web_analysis_text:
            # When web analysis fails, we can't extract brand visibility from search results
            # But we can provide a meaningful message about why the data is limited
            return VisualizationData(
                chart_type="bar_chart_brand_visibility",
                title="Top 5 Brands by LLM Search Visibility",
                x_axis_label="Brand Name",
                y_axis_label="Visibility Score (1-100)",
                top_5_brands=["Web analysis unavailable"],
                brand_scores=[
                    {
                        "brand_name": "Web analysis unavailable",
                        "visibility_score": 1,
                        "rank": 1,
                        "mentions": 0
                    }
                ],
                methodology_explanation="Web analysis failed, so brand visibility data could not be extracted from search results. The system fell back to ChatGPT knowledge only, which provides general information but not search-based visibility metrics."
            )
        elif "No brand information could be extracted" in web_analysis_text:
            # Handle the case where the LLM couldn't extract brand data
            return VisualizationData(
                chart_type="bar_chart_brand_visibility",
                title="Top 5 Brands by LLM Search Visibility",
                x_axis_label="Brand Name",
                y_axis_label="Visibility Score (1-100)",
                top_5_brands=["Brand data unavailable"],
                brand_scores=[
                    {
                        "brand_name": "Brand data unavailable",
                        "visibility_score": 1,
                        "rank": 1,
                        "mentions": 0
                    }
                ],
                methodology_explanation="The LLM was unable to extract brand information from the provided text. This may be due to insufficient content or formatting issues."
            )
        else:
            # Return a fallback object that conforms to the schema for other errors
            return VisualizationData(
                chart_type="bar_chart_brand_visibility",
                title="Top 5 Brands by LLM Search Visibility",
                x_axis_label="Brand Name",
                y_axis_label="Visibility Score (1-100)",
                top_5_brands=["Analysis error"],
                brand_scores=[
                    {
                        "brand_name": "Analysis error",
                        "visibility_score": 1,
                        "rank": 1,
                        "mentions": 0
                    }
                ],
                methodology_explanation=f"Data extraction failed due to an error: {e}"
            )
