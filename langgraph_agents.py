"""
LangGraph-Based Hotel Booking Agents
This replaces the manual orchestration in Agents.py with proper LangGraph workflows
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, TypedDict

import nest_asyncio
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

# Enable nested asyncio for better event loop handling
nest_asyncio.apply()

load_dotenv()


# Define the shared state for the workflow
class HotelBookingState(TypedDict):
    """Shared state across all agents in the LangGraph workflow"""

    user_query: str
    extracted_dates: Dict
    search_parameters: Dict
    search_results: Dict
    selected_hotel: Dict
    guest_info: Dict
    booking_result: Dict
    current_step: str
    error_message: str
    workflow_complete: bool
    debug_info: List[str]


class LangGraphHotelWorkflow:
    """Proper LangGraph implementation replacing manual agent orchestration"""

    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        if not self.google_api_key:
            raise ValueError("Set GOOGLE_API_KEY environment variable")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", api_key=self.google_api_key, temperature=0.1
        )

        # Initialize MCP client for tools
        self.mcp_client = None
        self.tools = []

        # Create the workflow graph
        self.workflow = self._create_workflow_graph()
        self.compiled_app = None

    async def setup_tools(self):
        """Setup MCP tools for the workflow"""
        if self.mcp_client is not None:
            return

        print("🔧 LangGraph: Setting up MCP client...")
        self.mcp_client = MultiServerMCPClient(
            {
                "hotel_booking": {
                    "command": "python",
                    "args": ["mcp_server.py"],
                    "transport": "stdio",
                }
            }
        )

        self.tools = await self.mcp_client.get_tools()
        print(
            f"✅ LangGraph: Loaded {len(self.tools)} tools: {[t.name for t in self.tools]}"
        )

    def _create_workflow_graph(self) -> StateGraph:
        """Create the LangGraph workflow with proper state management"""

        # Create StateGraph with our state schema
        workflow = StateGraph(HotelBookingState)

        # Add nodes (agents) to the graph
        workflow.add_node("date_extractor", self.date_extractor_node)
        workflow.add_node("query_analyzer", self.query_analyzer_node)
        workflow.add_node("hotel_searcher", self.hotel_searcher_node)
        workflow.add_node("availability_checker", self.availability_checker_node)
        workflow.add_node("booking_executor", self.booking_executor_node)
        workflow.add_node("error_handler", self.error_handler_node)

        # Define the workflow edges (routing logic)
        workflow.set_entry_point("date_extractor")

        # Date extractor -> Query analyzer
        workflow.add_edge("date_extractor", "query_analyzer")

        # Query analyzer -> Hotel searcher or error
        workflow.add_conditional_edges(
            "query_analyzer",
            self.should_search_hotels,
            {"search": "hotel_searcher", "error": "error_handler", "end": END},
        )

        # Hotel searcher -> Availability checker or end
        workflow.add_conditional_edges(
            "hotel_searcher",
            self.should_check_availability,
            {
                "check_availability": "availability_checker",
                "error": "error_handler",
                "end": END,
            },
        )

        # Availability checker -> Booking executor or end
        workflow.add_conditional_edges(
            "availability_checker",
            self.should_proceed_to_booking,
            {"book": "booking_executor", "end": END, "error": "error_handler"},
        )

        # Booking executor -> End
        workflow.add_edge("booking_executor", END)
        workflow.add_edge("error_handler", END)

        return workflow

    # Node implementations (agents as LangGraph nodes)
    async def date_extractor_node(self, state: HotelBookingState) -> HotelBookingState:
        """DateExtractor Agent as a LangGraph node"""
        print("📅 LangGraph Node: DateExtractor Agent")

        user_query = state["user_query"]
        today = datetime.now().date()
        debug_info = state.get("debug_info", [])
        debug_info.append(f"📅 DateExtractor processing: {user_query}")

        system_prompt = f"""You are a hotel booking date extraction specialist. 

TODAY'S DATE: {today.strftime("%Y-%m-%d")} ({today.strftime("%A, %B %d, %Y")})

TASK: Extract check-in and check-out dates from hotel booking queries.

RULES:
1. ALWAYS respond with ONLY valid JSON - no other text
2. Handle relative dates like "next week", "tomorrow", etc.
3. Convert durations: "2 days" = 2 nights stay
4. For date ranges like "july 25 to 26", use the exact dates given
5. If ambiguous, prefer later dates in 2025

REQUIRED JSON FORMAT:
{{
    "check_in": "YYYY-MM-DD",
    "check_out": "YYYY-MM-DD", 
    "confidence": "high|medium|low",
    "method": "method_used",
    "details": "explanation"
}}

EXAMPLES:
INPUT: "book hotel for 2 days from july 25 2025"
OUTPUT: {{"check_in": "2025-07-25", "check_out": "2025-07-27", "confidence": "high", "method": "explicit_start_plus_duration", "details": "Found start date july 25 2025 + 2 days duration"}}

INPUT: "july 25 to 26th 2025"  
OUTPUT: {{"check_in": "2025-07-25", "check_out": "2025-07-26", "confidence": "high", "method": "explicit_range", "details": "Found explicit date range july 25-26 2025"}}

RESPOND WITH ONLY THE JSON - NO OTHER TEXT!"""

        try:
            response = await self.llm.ainvoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"QUERY: {user_query}"},
                ]
            )

            content = response.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            elif content.startswith("```"):
                content = content.replace("```", "")
            content = content.strip()

            extracted_dates = json.loads(content)
            debug_info.append(
                f"📅 Extracted: {extracted_dates['check_in']} to {extracted_dates['check_out']} ({extracted_dates['confidence']})"
            )

            return {
                **state,
                "extracted_dates": extracted_dates,
                "current_step": "date_extraction_complete",
                "debug_info": debug_info,
            }

        except Exception as e:
            debug_info.append(f"❌ Date extraction failed: {str(e)}")
            # Intelligent fallback
            fallback_dates = self._intelligent_date_fallback(user_query, today)
            debug_info.append(
                f"📅 Using fallback: {fallback_dates['check_in']} to {fallback_dates['check_out']}"
            )

            return {
                **state,
                "extracted_dates": fallback_dates,
                "current_step": "date_extraction_fallback",
                "debug_info": debug_info,
            }

    def _intelligent_date_fallback(self, query: str, today: datetime.date) -> Dict:
        """Intelligent fallback for date extraction"""
        import re

        # Look for explicit years
        year_match = re.search(r"20\d{2}", query)
        target_year = int(year_match.group()) if year_match else 2025

        # Simple month detection
        month_patterns = {
            "january": 1,
            "jan": 1,
            "february": 2,
            "feb": 2,
            "march": 3,
            "mar": 3,
            "april": 4,
            "apr": 4,
            "may": 5,
            "june": 6,
            "jun": 6,
            "july": 7,
            "jul": 7,
            "august": 8,
            "aug": 8,
            "september": 9,
            "sep": 9,
            "october": 10,
            "oct": 10,
            "november": 11,
            "nov": 11,
            "december": 12,
            "dec": 12,
        }

        found_month = None
        found_day = None

        query_lower = query.lower()
        for month_name, month_num in month_patterns.items():
            if month_name in query_lower:
                found_month = month_num
                # Look for day numbers
                day_match = re.search(rf"{month_name}\s+(\d{{1,2}})", query_lower)
                if day_match:
                    found_day = int(day_match.group(1))
                break

        if found_month and found_day:
            try:
                check_in = datetime(target_year, found_month, found_day).date()
                check_out = check_in + timedelta(days=2)  # Default 2 nights

                return {
                    "check_in": check_in.strftime("%Y-%m-%d"),
                    "check_out": check_out.strftime("%Y-%m-%d"),
                    "confidence": "medium",
                    "method": "regex_fallback",
                    "details": f"Fallback extraction found {month_name} {found_day}, {target_year}",
                }
            except ValueError:
                pass

        # Ultimate fallback - today + 7 days for 2 nights
        check_in = today + timedelta(days=7)
        check_out = check_in + timedelta(days=2)

        return {
            "check_in": check_in.strftime("%Y-%m-%d"),
            "check_out": check_out.strftime("%Y-%m-%d"),
            "confidence": "low",
            "method": "default_fallback",
            "details": "No dates found, using default: next week for 2 nights",
        }

    async def query_analyzer_node(self, state: HotelBookingState) -> HotelBookingState:
        """Query Analyzer Agent as a LangGraph node"""
        print("🧠 LangGraph Node: Query Analyzer")

        user_query = state["user_query"]
        debug_info = state.get("debug_info", [])
        debug_info.append(f"🧠 Query Analyzer processing: {user_query}")

        try:
            # Setup tools with better error handling
            await self.setup_tools()

            system_prompt = """You are a hotel search query analyzer. Analyze user queries to determine search parameters.

RESPONSIBILITIES:
1. Determine if this is a hotel booking request
2. Extract location, budget, preferences
3. Map locations: "sf"→"San Francisco", "nyc"→"New York", "la"→"Los Angeles"
4. Identify amenities: "beach/pier"→"Beach Access", "gym"→"Gym", "spa"→"Spa"
5. Calculate budget constraints

AVAILABLE TOOLS:
- search_hotels(location, max_price, amenities, min_rating) - Main hotel search
- get_hotel_details(hotel_id) - Get specific hotel information  
- check_availability(hotel_id, check_in, check_out, guests) - Check room availability
- list_all_bookings() - View existing bookings
- get_booking_statistics() - Get booking analytics

INSTRUCTIONS:
1. If user wants hotels/accommodation, call search_hotels with appropriate parameters
2. For non-hotel queries, respond conversationally without tools
3. Extract search parameters accurately"""

            # Use LLM with tools with proper error handling
            try:
                llm_with_tools = self.llm.bind_tools(self.tools)

                response = await llm_with_tools.ainvoke(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_query},
                    ]
                )

                has_tool_calls = hasattr(response, "tool_calls") and response.tool_calls
                debug_info.append(
                    f"🧠 Analysis complete. Tool calls: {len(response.tool_calls) if has_tool_calls else 0}"
                )

                search_params = {
                    "has_hotel_intent": has_tool_calls,
                    "tool_calls": response.tool_calls if has_tool_calls else [],
                    "response": response.content,
                    "intent_type": "hotel_search" if has_tool_calls else "conversation",
                }

                return {
                    **state,
                    "search_parameters": search_params,
                    "current_step": "query_analysis_complete",
                    "debug_info": debug_info,
                }

            except Exception as llm_error:
                debug_info.append(f"❌ LLM invocation failed: {str(llm_error)}")
                # Enhanced fallback: extract parameters and create tool calls
                hotel_keywords = [
                    "hotel",
                    "booking",
                    "book",
                    "stay",
                    "reservation",
                    "room",
                ]
                has_hotel_intent = any(
                    word in user_query.lower() for word in hotel_keywords
                )

                if has_hotel_intent:
                    # Create fallback search parameters
                    location = "San Francisco, CA"  # Default to SF since we have beach hotels there
                    max_price = 1000.0  # Default high price
                    amenities = ""

                    # Try to extract location from query
                    location_map = {
                        "sf": "San Francisco, CA",
                        "san francisco": "San Francisco, CA",
                        "nyc": "New York, NY",
                        "new york": "New York, NY",
                        "miami": "Miami, FL",
                        "la": "Los Angeles, CA",
                        "denver": "Denver, CO",
                        "chicago": "Chicago, IL",
                        "boston": "Boston, MA",
                    }

                    query_lower = user_query.lower()
                    for key, value in location_map.items():
                        if key in query_lower:
                            location = value
                            break

                    # Extract budget if mentioned
                    import re

                    budget_match = re.search(r"\$?(\d+)", user_query)
                    if budget_match:
                        max_price = float(budget_match.group(1))
                        debug_info.append(f"💰 Extracted budget: ${max_price}")

                    # Extract amenities
                    if any(
                        word in query_lower
                        for word in ["beach", "ocean", "sea", "water"]
                    ):
                        amenities = "Beach Access"
                        debug_info.append("🏖️ Detected beach preference")
                    elif "spa" in query_lower:
                        amenities = "Spa"
                    elif "gym" in query_lower:
                        amenities = "Gym"

                    # Create tool call for fallback search
                    tool_calls = [
                        {
                            "name": "search_hotels",
                            "args": {
                                "location": location,
                                "max_price": max_price,
                                "amenities": amenities,
                                "min_rating": 3.0,
                            },
                        }
                    ]

                    debug_info.append(
                        f"🔧 Fallback search: {location}, max ${max_price}, amenities: {amenities}"
                    )

                    search_params = {
                        "has_hotel_intent": True,
                        "tool_calls": tool_calls,
                        "response": f"Fallback search for {location} with budget ${max_price}",
                        "intent_type": "hotel_search",
                        "location": location,
                        "max_price": max_price,
                        "amenities": amenities,
                    }
                else:
                    search_params = {
                        "has_hotel_intent": False,
                        "tool_calls": [],
                        "response": f"No hotel intent detected in: {user_query}",
                        "intent_type": "conversation",
                    }

                return {
                    **state,
                    "search_parameters": search_params,
                    "current_step": "query_analysis_complete",
                    "debug_info": debug_info,
                }

        except Exception as e:
            debug_info.append(f"❌ Query analysis failed: {str(e)}")
            return {
                **state,
                "error_message": f"Query analysis failed: {str(e)}",
                "current_step": "error",
                "debug_info": debug_info,
            }

    async def hotel_searcher_node(self, state: HotelBookingState) -> HotelBookingState:
        """Hotel Searcher as a LangGraph node"""
        print("🔍 LangGraph Node: Hotel Searcher")

        search_params = state["search_parameters"]
        tool_calls = search_params.get("tool_calls", [])
        debug_info = state.get("debug_info", [])
        debug_info.append(f"🔍 Executing {len(tool_calls)} hotel search tool calls")

        try:
            # Execute search tools
            search_results = []
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                debug_info.append(f"🔧 Calling {tool_name} with args: {tool_args}")

                tool = next((t for t in self.tools if t.name == tool_name), None)
                if tool:
                    result = await tool.ainvoke(tool_args)
                    search_results.append(
                        {
                            "tool": tool_name,
                            "args": tool_args,
                            "result": result,
                            "success": True,
                        }
                    )
                    debug_info.append(f"✅ {tool_name} succeeded")
                else:
                    debug_info.append(f"❌ Tool {tool_name} not found")

            # Parse hotel results
            hotels = []
            message = "No hotels found"

            for result in search_results:
                if result["tool"] == "search_hotels" and result["success"]:
                    try:
                        hotel_data = (
                            json.loads(result["result"])
                            if isinstance(result["result"], str)
                            else result["result"]
                        )
                        if "hotels" in hotel_data:
                            hotels.extend(hotel_data["hotels"])
                            message = f"Found {len(hotels)} hotels"
                        debug_info.append(f"🏨 Parsed {len(hotels)} hotels from search")
                    except json.JSONDecodeError as e:
                        debug_info.append(f"❌ Failed to parse hotel results: {str(e)}")

            return {
                **state,
                "search_results": {
                    "hotels": hotels,
                    "message": message,
                    "tool_results": search_results,
                    "type": "hotel_results" if hotels else "no_results",
                },
                "current_step": "hotel_search_complete",
                "debug_info": debug_info,
            }

        except Exception as e:
            debug_info.append(f"❌ Hotel search failed: {str(e)}")
            return {
                **state,
                "error_message": f"Hotel search failed: {str(e)}",
                "current_step": "error",
                "debug_info": debug_info,
            }

    async def availability_checker_node(
        self, state: HotelBookingState
    ) -> HotelBookingState:
        """Availability Checker as a LangGraph node"""
        print("📋 LangGraph Node: Availability Checker")

        hotels = state["search_results"].get("hotels", [])
        extracted_dates = state["extracted_dates"]
        debug_info = state.get("debug_info", [])

        if not hotels:
            debug_info.append("📋 No hotels to check availability for")
            return {
                **state,
                "current_step": "availability_check_skipped",
                "debug_info": debug_info,
            }

        try:
            # Check availability for the first hotel (can be enhanced for multiple)
            hotel = hotels[0]
            debug_info.append(
                f"📋 Checking availability for {hotel.get('name', 'Unknown Hotel')}"
            )

            check_availability_tool = next(
                (t for t in self.tools if t.name == "check_availability"), None
            )

            if check_availability_tool:
                availability_result = await check_availability_tool.ainvoke(
                    {
                        "hotel_id": hotel["id"],
                        "check_in": extracted_dates["check_in"],
                        "check_out": extracted_dates["check_out"],
                        "guests": 2,
                    }
                )

                debug_info.append(f"📋 Availability check complete for {hotel['name']}")

                return {
                    **state,
                    "selected_hotel": {
                        **hotel,
                        "availability_result": availability_result,
                        "available": True,  # Simplified for demo
                    },
                    "current_step": "availability_check_complete",
                    "debug_info": debug_info,
                }
            else:
                debug_info.append("❌ Availability check tool not found")
                return {
                    **state,
                    "selected_hotel": hotel,
                    "current_step": "availability_check_skipped",
                    "debug_info": debug_info,
                }

        except Exception as e:
            debug_info.append(f"❌ Availability check failed: {str(e)}")
            return {
                **state,
                "error_message": f"Availability check failed: {str(e)}",
                "current_step": "error",
                "debug_info": debug_info,
            }

    async def booking_executor_node(
        self, state: HotelBookingState
    ) -> HotelBookingState:
        """Booking Executor as a LangGraph node"""
        print("🏨 LangGraph Node: Booking Executor")

        selected_hotel = state["selected_hotel"]
        extracted_dates = state["extracted_dates"]
        guest_info = state.get("guest_info", {})
        debug_info = state.get("debug_info", [])

        try:
            debug_info.append(
                f"🏨 Booking {selected_hotel.get('name', 'Unknown Hotel')}"
            )

            book_tool = next((t for t in self.tools if t.name == "book_hotel"), None)
            if not book_tool:
                raise ValueError("Booking tool not available")

            # Try to get room from availability result, otherwise use default
            room_id = None
            if "availability_result" in selected_hotel:
                try:
                    availability_data = selected_hotel["availability_result"]
                    if isinstance(availability_data, str):
                        availability_data = json.loads(availability_data)

                    available_rooms = availability_data.get("available_rooms", [])
                    if available_rooms:
                        # Use the first available room
                        room_id = available_rooms[0]["id"]
                        debug_info.append(f"🏨 Using available room: {room_id}")
                    else:
                        debug_info.append(
                            "⚠️ No available rooms found in availability check"
                        )
                except Exception as e:
                    debug_info.append(f"⚠️ Error parsing availability data: {str(e)}")

            # Fallback: generate room ID if not found from availability
            if not room_id:
                hotel_number = selected_hotel["id"].replace("hotel_", "")
                room_id = f"room_{hotel_number}_1"
                debug_info.append(f"🏨 Using fallback room: {room_id}")

            booking_args = {
                "hotel_id": selected_hotel["id"],
                "room_id": room_id,
                "guest_name": guest_info.get("name", "Demo User"),
                "guest_email": guest_info.get("email", "demo@example.com"),
                "check_in": extracted_dates["check_in"],
                "check_out": extracted_dates["check_out"],
            }

            debug_info.append(f"🏨 Executing booking with args: {booking_args}")
            booking_result = await book_tool.ainvoke(booking_args)
            debug_info.append("🎉 Booking completed successfully")

            return {
                **state,
                "booking_result": {
                    "success": True,
                    "result": booking_result,
                    "hotel_name": selected_hotel.get("name"),
                    "dates": f"{extracted_dates['check_in']} to {extracted_dates['check_out']}",
                },
                "workflow_complete": True,
                "current_step": "booking_complete",
                "debug_info": debug_info,
            }

        except Exception as e:
            debug_info.append(f"❌ Booking failed: {str(e)}")
            return {
                **state,
                "error_message": f"Booking failed: {str(e)}",
                "current_step": "error",
                "debug_info": debug_info,
            }

    async def error_handler_node(self, state: HotelBookingState) -> HotelBookingState:
        """Error Handler node"""
        error_msg = state.get("error_message", "Unknown error occurred")
        print(f"❌ LangGraph Node: Error Handler - {error_msg}")

        debug_info = state.get("debug_info", [])
        debug_info.append(f"❌ Error handled: {error_msg}")

        return {
            **state,
            "workflow_complete": True,
            "current_step": "error_handled",
            "debug_info": debug_info,
        }

    # Conditional edge functions
    def should_search_hotels(self, state: HotelBookingState) -> str:
        """Decide if we should search for hotels"""
        if state.get("error_message"):
            return "error"

        search_params = state.get("search_parameters", {})
        if search_params.get("has_hotel_intent"):
            return "search"

        return "end"

    def should_check_availability(self, state: HotelBookingState) -> str:
        """Decide if we should check availability"""
        if state.get("error_message"):
            return "error"

        hotels = state.get("search_results", {}).get("hotels", [])
        if hotels:
            return "check_availability"

        return "end"

    def should_proceed_to_booking(self, state: HotelBookingState) -> str:
        """Decide if we should proceed to booking"""
        if state.get("error_message"):
            return "error"

        # For search-only workflow, don't auto-book
        # This would typically check user confirmation or guest info
        selected_hotel = state.get("selected_hotel")
        guest_info = state.get("guest_info", {})

        # Only proceed to booking if guest info is provided
        if selected_hotel and guest_info.get("name") and guest_info.get("email"):
            return "book"

        return "end"

    async def run_search_workflow(self, user_query: str) -> Dict:
        """Run the hotel search workflow (without booking)"""

        if not self.compiled_app:
            memory = MemorySaver()
            self.compiled_app = self.workflow.compile(checkpointer=memory)

        # Initial state for search-only workflow
        initial_state = {
            "user_query": user_query,
            "extracted_dates": {},
            "search_parameters": {},
            "search_results": {},
            "selected_hotel": {},
            "guest_info": {},  # Empty for search-only
            "booking_result": {},
            "current_step": "starting",
            "error_message": "",
            "workflow_complete": False,
            "debug_info": [],
        }

        # Run the workflow
        config = {"configurable": {"thread_id": f"search_{hash(user_query)}"}}
        final_state = await self.compiled_app.ainvoke(initial_state, config)

        return final_state

    async def run_booking_workflow(
        self, user_query: str, selected_hotel: Dict, guest_info: Dict
    ) -> Dict:
        """Run the complete booking workflow with user selection"""

        if not self.compiled_app:
            memory = MemorySaver()
            self.compiled_app = self.workflow.compile(checkpointer=memory)

        # Initial state for booking workflow
        initial_state = {
            "user_query": user_query,
            "extracted_dates": {},
            "search_parameters": {"has_hotel_intent": False},  # Skip search
            "search_results": {"hotels": [selected_hotel]},
            "selected_hotel": selected_hotel,
            "guest_info": guest_info,
            "booking_result": {},
            "current_step": "starting",
            "error_message": "",
            "workflow_complete": False,
            "debug_info": [],
        }

        # Run the workflow starting from date extraction
        config = {
            "configurable": {
                "thread_id": f"booking_{hash(user_query + selected_hotel['id'])}"
            }
        }
        final_state = await self.compiled_app.ainvoke(initial_state, config)

        return final_state


# Global workflow instance
_workflow_instance = None


async def get_workflow() -> LangGraphHotelWorkflow:
    """Get or create the global workflow instance"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = LangGraphHotelWorkflow()
        await _workflow_instance.setup_tools()
    return _workflow_instance


# Streamlit integration functions (replaces functions in Agents.py)
async def orchestrate_hotel_search(user_query: str) -> Dict:
    """LangGraph-powered hotel search (replaces the manual orchestration)"""
    workflow = await get_workflow()
    result = await workflow.run_search_workflow(user_query)

    # Format result for Streamlit compatibility
    return {
        "type": result["search_results"].get("type", "conversation"),
        "message": result["search_results"].get("message", "Search completed"),
        "hotels": result["search_results"].get("hotels", []),
        "date_extraction": result.get("extracted_dates", {}),
        "debug_info": result.get("debug_info", []),
        "workflow_state": result,
    }


async def book_hotel_reservation(
    selected_hotel: Dict,
    guest_name: str,
    guest_email: str,
    check_in: str,
    check_out: str,
) -> Dict:
    """LangGraph-powered hotel booking (replaces BookingAgent)"""
    workflow = await get_workflow()

    guest_info = {"name": guest_name, "email": guest_email}

    # Create a query for the booking workflow
    query = f"Book {selected_hotel['name']} from {check_in} to {check_out}"

    result = await workflow.run_booking_workflow(query, selected_hotel, guest_info)

    # Format result for Streamlit compatibility
    if result.get("booking_result", {}).get("success"):
        return {
            "success": True,
            "message": f"✅ Successfully booked {selected_hotel['name']}",
            "hotel_name": selected_hotel["name"],
            "guest_name": guest_name,
            "booking_details": result["booking_result"],
            "debug_info": result.get("debug_info", []),
        }
    else:
        return {
            "success": False,
            "message": result.get("error_message", "Booking failed"),
            "debug_info": result.get("debug_info", []),
        }


async def list_all_hotel_bookings() -> Dict:
    """Get all hotel bookings using MCP tools"""
    try:
        workflow = await get_workflow()

        # Use the MCP tools to get bookings
        if workflow.mcp_client and workflow.tools:
            # Find the list_all_bookings tool
            list_bookings_tool = next(
                (t for t in workflow.tools if t.name == "list_all_bookings"), None
            )

            if list_bookings_tool:
                result = await list_bookings_tool.ainvoke({})

                # Parse the JSON response from MCP tool
                import json

                if isinstance(result, str):
                    bookings_data = json.loads(result)
                else:
                    bookings_data = result

                return {
                    "success": True,
                    "bookings": bookings_data.get("bookings", []),
                    "message": f"Found {len(bookings_data.get('bookings', []))} bookings",
                }
            else:
                return {
                    "success": False,
                    "bookings": [],
                    "message": "list_all_bookings tool not found",
                }
        else:
            return {
                "success": False,
                "bookings": [],
                "message": "MCP client not available",
            }

    except Exception as e:
        return {
            "success": False,
            "bookings": [],
            "message": f"Error retrieving bookings: {str(e)}",
        }


async def cancel_hotel_booking(booking_id: str) -> Dict:
    """Cancel a hotel booking using MCP tools"""
    try:
        workflow = await get_workflow()

        # Use the MCP tools to cancel booking
        if workflow.mcp_client and workflow.tools:
            # Find the cancel_booking tool
            cancel_tool = next(
                (t for t in workflow.tools if t.name == "cancel_booking"), None
            )

            if cancel_tool:
                result = await cancel_tool.ainvoke({"booking_id": booking_id})

                # Parse the JSON response from MCP tool
                import json

                if isinstance(result, str):
                    cancel_data = json.loads(result)
                else:
                    cancel_data = result

                return {
                    "success": cancel_data.get("success", False),
                    "message": cancel_data.get("message", "Booking cancelled"),
                    "refund_amount": cancel_data.get("refund_amount", 0),
                }
            else:
                return {"success": False, "message": "cancel_booking tool not found"}
        else:
            return {"success": False, "message": "MCP client not available"}

    except Exception as e:
        return {"success": False, "message": f"Error cancelling booking: {str(e)}"}


async def get_hotel_booking_statistics() -> Dict:
    """Get booking statistics using MCP tools"""
    try:
        workflow = await get_workflow()

        # Use the MCP tools to get statistics
        if workflow.mcp_client and workflow.tools:
            # Find the get_booking_statistics tool
            stats_tool = next(
                (t for t in workflow.tools if t.name == "get_booking_statistics"), None
            )

            if stats_tool:
                result = await stats_tool.ainvoke({})

                # Parse the JSON response from MCP tool
                import json

                if isinstance(result, str):
                    stats_data = json.loads(result)
                else:
                    stats_data = result

                return {
                    "success": True,
                    "statistics": stats_data.get("statistics", {}),
                    "message": "Statistics retrieved successfully",
                }
            else:
                return {
                    "success": False,
                    "statistics": {},
                    "message": "get_booking_statistics tool not found",
                }
        else:
            return {
                "success": False,
                "statistics": {},
                "message": "MCP client not available",
            }

    except Exception as e:
        return {
            "success": False,
            "statistics": {},
            "message": f"Error retrieving statistics: {str(e)}",
        }


# Demo function
async def demo_langgraph_workflow():
    """Demo the complete LangGraph workflow"""
    print("🎯 DEMO: LangGraph Hotel Booking Workflow")
    print("=" * 60)

    workflow = await get_workflow()

    # Demo search workflow
    query = "book me a hotel in sf for 2 days from july 25 2025 with beach access"
    print(f"🔍 Running search workflow: {query}")

    search_result = await workflow.run_search_workflow(query)

    print("\n📊 Search Workflow Complete:")
    print(f"   • Final Step: {search_result['current_step']}")
    print(
        f"   • Hotels Found: {len(search_result.get('search_results', {}).get('hotels', []))}"
    )
    print(f"   • Extracted Dates: {search_result.get('extracted_dates', {})}")

    # Debug info
    for debug in search_result.get("debug_info", []):
        print(f"   🐛 {debug}")

    # Demo booking workflow if hotels found
    hotels = search_result.get("search_results", {}).get("hotels", [])
    if hotels:
        print(f"\n🏨 Running booking workflow for: {hotels[0]['name']}")

        guest_info = {"name": "John Doe", "email": "john@example.com"}
        booking_result = await workflow.run_booking_workflow(
            query, hotels[0], guest_info
        )

        print(f"   • Booking Complete: {booking_result['workflow_complete']}")
        print(
            f"   • Success: {booking_result.get('booking_result', {}).get('success', False)}"
        )

        for debug in booking_result.get("debug_info", []):
            print(f"   🐛 {debug}")


if __name__ == "__main__":
    asyncio.run(demo_langgraph_workflow())
