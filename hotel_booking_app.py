"""
Hotel Booking Streamlit App
Integrates with LangGraph workflow for intelligent hotel search and booking
"""

import asyncio
from datetime import datetime

import nest_asyncio
import pandas as pd
import streamlit as st

from langgraph_agents import (
    book_hotel_reservation,
    cancel_hotel_booking,
    get_hotel_booking_statistics,
    list_all_hotel_bookings,
    orchestrate_hotel_search,
)

# Enable nested asyncio for Streamlit compatibility
nest_asyncio.apply()

# Configure Streamlit page
st.set_page_config(
    page_title="🏨 Hotel Booking Assistant",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .hotel-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        background-color: #f9f9f9;
    }
    .hotel-name {
        font-size: 24px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 10px;
    }
    .hotel-rating {
        color: #f39c12;
        font-size: 18px;
        margin-bottom: 10px;
    }
    .hotel-price {
        font-size: 20px;
        font-weight: bold;
        color: #27ae60;
        margin-bottom: 10px;
    }
    .amenities-tag {
        background-color: #3498db;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        margin: 2px;
        font-size: 12px;
    }
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        color: #155724;
    }
    .error-message {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        color: #721c24;
    }
</style>
""",
    unsafe_allow_html=True,
)


def init_session_state():
    """Initialize session state variables"""
    if "search_results" not in st.session_state:
        st.session_state.search_results = None
    if "selected_hotel" not in st.session_state:
        st.session_state.selected_hotel = None
    if "booking_step" not in st.session_state:
        st.session_state.booking_step = "search"
    if "booking_result" not in st.session_state:
        st.session_state.booking_result = None


def display_hotel_card(hotel, index):
    """Display a hotel as a card with selection button"""
    with st.container():
        st.markdown(
            f"""
        <div class="hotel-card">
            <div class="hotel-name">{hotel["name"]}</div>
            <div class="hotel-rating">⭐ {hotel["rating"]}/5.0</div>
            <div class="hotel-price">${hotel["price_per_night"]}/night</div>
            <p><strong>📍 Location:</strong> {hotel["location"]}</p>
            <p><strong>📋 Description:</strong> {hotel["description"]}</p>
            <p><strong>🛏️ Available Rooms:</strong> {hotel["available_rooms"]}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Display amenities as tags
        if hotel.get("amenities"):
            st.write("**🏊 Amenities:**")
            amenities_html = "".join(
                [
                    f'<span class="amenities-tag">{amenity}</span>'
                    for amenity in hotel["amenities"]
                ]
            )
            st.markdown(amenities_html, unsafe_allow_html=True)

        # Selection button
        col1, col2, col3 = st.columns([1, 1, 2])
        with col2:
            if st.button("Select This Hotel", key=f"select_{index}", type="primary"):
                st.session_state.selected_hotel = hotel
                st.session_state.booking_step = "guest_info"
                st.rerun()


def run_async_safely(coroutine):
    """Safely run async functions in Streamlit context with nest_asyncio"""
    try:
        # With nest_asyncio applied, we can directly use asyncio.run
        # even in contexts where an event loop is already running
        return asyncio.run(coroutine)
    except Exception as e:
        st.error(f"❌ Async execution failed: {str(e)}")
        st.error("Please check that your GOOGLE_API_KEY is set correctly.")
        with st.expander("🔍 Detailed Error", expanded=False):
            import traceback

            st.code(traceback.format_exc())
        raise e


async def search_hotels_async(query):
    """Async wrapper for hotel search"""
    return await orchestrate_hotel_search(query)


async def book_hotel_async(
    selected_hotel, guest_name, guest_email, check_in, check_out
):
    """Async wrapper for hotel booking"""
    return await book_hotel_reservation(
        selected_hotel, guest_name, guest_email, check_in, check_out
    )


async def get_bookings_async():
    """Async wrapper for getting all bookings"""
    return await list_all_hotel_bookings()


async def cancel_booking_async(booking_id):
    """Async wrapper for canceling booking"""
    return await cancel_hotel_booking(booking_id)


async def get_stats_async():
    """Async wrapper for getting booking statistics"""
    return await get_hotel_booking_statistics()


def main():
    """Main Streamlit application"""
    init_session_state()

    # Title and description
    st.title("🏨 Hotel Booking Assistant")
    st.markdown("### Powered by LangGraph AI Workflow")
    st.markdown("Search for hotels using natural language and book your perfect stay!")

    # Sidebar for navigation
    with st.sidebar:
        st.header("📖 Navigation")
        page = st.radio(
            "Choose an option:",
            ["🔍 Search & Book Hotels", "📋 My Bookings", "📊 Statistics"],
            index=0,
        )

        st.markdown("---")
        st.header("💡 Example Queries")
        st.markdown("""
        - "book me a hotel in sf for 2 days from july 25 2025 with beach access"
        - "find hotels in miami for next week"
        - "cheap hotel in nyc for 3 nights"
        - "luxury hotel in denver with spa"
        - "business hotel in chicago"
        """)

        st.markdown("---")
        st.header("🔧 Debug Mode")
        debug_mode = st.checkbox("Enable Debug Information", value=False)

    # Main content based on selected page
    if page == "🔍 Search & Book Hotels":
        handle_search_and_booking(debug_mode)
    elif page == "📋 My Bookings":
        handle_bookings_management()
    elif page == "📊 Statistics":
        handle_statistics()


def handle_search_and_booking(debug_mode=False):
    """Handle the search and booking workflow"""

    if st.session_state.booking_step == "search":
        st.header("🔍 Search Hotels")

        # Search input
        user_query = st.text_input(
            "Enter your hotel search query:",
            placeholder="e.g., hotel in san francisco for 2 days from july 25 2025 with beach access",
            help="Use natural language to describe what you're looking for!",
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            search_button = st.button("🔍 Search Hotels", type="primary")

        if search_button and user_query:
            with st.spinner(
                "🤖 AI is analyzing your request and searching for hotels..."
            ):
                try:
                    # Run the async search safely
                    search_results = run_async_safely(search_hotels_async(user_query))
                    st.session_state.search_results = search_results

                    # Debug information
                    if debug_mode:
                        with st.expander("🐛 Full Response Debug", expanded=False):
                            st.json(search_results)

                    # Check if we have hotels or if there's an error
                    if (
                        search_results.get("hotels")
                        and len(search_results["hotels"]) > 0
                    ):
                        st.success("✅ Search completed successfully!")
                    elif search_results.get("workflow_state", {}).get("error_message"):
                        st.error(
                            f"❌ {search_results['workflow_state']['error_message']}"
                        )
                    else:
                        st.warning("⚠️ Search completed but no results found.")

                    # Always show debug info if available and debug mode is on
                    if debug_mode and search_results.get("debug_info"):
                        with st.expander("🐛 Debug Information", expanded=True):
                            for debug in search_results["debug_info"]:
                                st.write(f"• {debug}")

                except Exception as e:
                    st.error(f"❌ Error during search: {str(e)}")
                    if debug_mode:
                        with st.expander("🔍 Error Details", expanded=True):
                            import traceback

                            st.code(traceback.format_exc())

        # Display search results
        if st.session_state.search_results:
            results = st.session_state.search_results

            if results.get("hotels") and len(results["hotels"]) > 0:
                st.header("🏨 Available Hotels")
                st.write(
                    f"Found **{len(results['hotels'])}** hotels matching your criteria:"
                )

                # Display extracted dates if available
                if results.get("date_extraction"):
                    dates = results["date_extraction"]
                    if dates:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if dates.get("check_in"):
                                st.info(f"📅 **Check-in:** {dates['check_in']}")
                        with col2:
                            if dates.get("check_out"):
                                st.info(f"📅 **Check-out:** {dates['check_out']}")
                        with col3:
                            if dates.get("confidence"):
                                st.info(f"🎯 **Confidence:** {dates['confidence']}")

                # Display search parameters from workflow state if available
                workflow_state = results.get("workflow_state", {})
                if workflow_state.get("search_parameters"):
                    params = workflow_state["search_parameters"]
                    if params.get("location"):
                        st.success(f"📍 **Searching in:** {params['location']}")

                # Display hotels
                for i, hotel in enumerate(results["hotels"]):
                    display_hotel_card(hotel, i)

            else:
                st.warning(
                    "⚠️ No hotels found matching your criteria. Try adjusting your search."
                )

                # Show debug information if available
                if debug_mode:
                    if results.get("debug_info"):
                        with st.expander("🐛 Debug Information", expanded=True):
                            for debug in results["debug_info"]:
                                st.write(f"• {debug}")

                    # Show workflow state for debugging
                    if results.get("workflow_state"):
                        with st.expander("🔍 Workflow State", expanded=True):
                            st.json(results["workflow_state"])
                else:
                    st.info("💡 Enable debug mode in the sidebar for more information.")

    elif st.session_state.booking_step == "guest_info":
        handle_guest_info_step()

    elif st.session_state.booking_step == "confirmation":
        handle_booking_confirmation()


def handle_guest_info_step():
    """Handle guest information collection"""
    st.header("👤 Guest Information")

    if st.session_state.selected_hotel:
        hotel = st.session_state.selected_hotel

        # Display selected hotel summary
        st.markdown(
            f"""
        <div class="success-message">
            <h4>🏨 Selected Hotel: {hotel["name"]}</h4>
            <p>📍 {hotel["location"]} | ⭐ {hotel["rating"]}/5.0 | 💰 ${hotel["price_per_night"]}/night</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Guest information form
        with st.form("guest_info_form"):
            st.subheader("📝 Please provide your details:")

            col1, col2 = st.columns(2)
            with col1:
                guest_name = st.text_input("Full Name *", placeholder="John Doe")
            with col2:
                guest_email = st.text_input(
                    "Email Address *", placeholder="john@example.com"
                )

            # Date information (extracted from search)
            search_results = st.session_state.search_results
            check_in = ""
            check_out = ""

            if search_results and search_results.get("date_extraction"):
                dates = search_results["date_extraction"]
                check_in = dates.get("check_in", "")
                check_out = dates.get("check_out", "")
            elif search_results and search_results.get("workflow_state", {}).get(
                "extracted_dates"
            ):
                dates = search_results["workflow_state"]["extracted_dates"]
                check_in = dates.get("check_in", "")
                check_out = dates.get("check_out", "")

            col3, col4 = st.columns(2)
            with col3:
                try:
                    default_checkin = (
                        datetime.strptime(check_in, "%Y-%m-%d").date()
                        if check_in
                        else datetime.now().date()
                    )
                except:
                    default_checkin = datetime.now().date()
                check_in_date = st.date_input("Check-in Date", value=default_checkin)
            with col4:
                try:
                    default_checkout = (
                        datetime.strptime(check_out, "%Y-%m-%d").date()
                        if check_out
                        else datetime.now().date()
                    )
                except:
                    default_checkout = datetime.now().date()
                check_out_date = st.date_input("Check-out Date", value=default_checkout)

            # Form submission
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.form_submit_button("⬅️ Back to Search", type="secondary"):
                    st.session_state.booking_step = "search"
                    st.session_state.selected_hotel = None
                    st.rerun()

            with col3:
                if st.form_submit_button("📋 Confirm Booking", type="primary"):
                    if guest_name and guest_email:
                        # Proceed with booking
                        with st.spinner("🤖 Processing your booking..."):
                            try:
                                booking_result = run_async_safely(
                                    book_hotel_async(
                                        hotel,
                                        guest_name,
                                        guest_email,
                                        check_in_date.strftime("%Y-%m-%d"),
                                        check_out_date.strftime("%Y-%m-%d"),
                                    )
                                )
                                st.session_state.booking_result = booking_result
                                st.session_state.booking_step = "confirmation"
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Booking failed: {str(e)}")
                                with st.expander("🔍 Error Details", expanded=False):
                                    import traceback

                                    st.code(traceback.format_exc())
                    else:
                        st.error("❌ Please fill in all required fields.")


def handle_booking_confirmation():
    """Handle booking confirmation display"""
    st.header("✅ Booking Confirmation")

    if st.session_state.booking_result:
        result = st.session_state.booking_result

        if result.get("success"):
            # Handle successful booking
            booking_details = result.get("booking_details", {})

            st.markdown(
                f"""
            <div class="success-message">
                <h3>🎉 Booking Confirmed!</h3>
                <p><strong>Hotel:</strong> {result.get("hotel_name", "N/A")}</p>
                <p><strong>Guest:</strong> {result.get("guest_name", "N/A")}</p>
                <p><strong>Message:</strong> {result.get("message", "Booking successful")}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Show booking details if available
            if booking_details:
                with st.expander("📋 Booking Details", expanded=True):
                    st.json(booking_details)

            st.balloons()

        else:
            st.markdown(
                f"""
            <div class="error-message">
                <h3>❌ Booking Failed</h3>
                <p>{result.get("message", "Unknown error occurred")}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Show debug info if available
            if result.get("debug_info"):
                with st.expander("🐛 Debug Information", expanded=False):
                    for debug in result["debug_info"]:
                        st.write(f"• {debug}")

    # Reset button
    if st.button("🔍 Search Again", type="primary"):
        st.session_state.booking_step = "search"
        st.session_state.selected_hotel = None
        st.session_state.search_results = None
        st.session_state.booking_result = None
        st.rerun()


def handle_bookings_management():
    """Handle bookings management page"""
    st.header("📋 My Bookings")

    # Fetch all bookings
    if st.button("🔄 Refresh Bookings"):
        with st.spinner("Loading bookings..."):
            try:
                bookings_result = run_async_safely(get_bookings_async())
                st.session_state.all_bookings = bookings_result
            except Exception as e:
                st.error(f"Error loading bookings: {str(e)}")

    # Display bookings
    if hasattr(st.session_state, "all_bookings") and st.session_state.all_bookings:
        result = st.session_state.all_bookings

        if result.get("success") and result.get("bookings"):
            bookings = result["bookings"]

            st.write(f"Total bookings: **{len(bookings)}**")

            # Convert to DataFrame for better display
            df_data = []
            for booking in bookings:
                df_data.append(
                    {
                        "Booking ID": booking.get("id", ""),
                        "Hotel": booking.get("hotel_name", ""),
                        "Guest": booking.get("guest_name", ""),
                        "Check-in": booking.get("check_in", ""),
                        "Check-out": booking.get("check_out", ""),
                        "Total Price": f"${booking.get('total_price', 0)}",
                        "Status": booking.get("status", ""),
                    }
                )

            if df_data:
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)

                # Cancellation section
                st.subheader("❌ Cancel Booking")
                booking_ids = [booking.get("id", "") for booking in bookings]
                selected_booking = st.selectbox(
                    "Select booking to cancel:", booking_ids
                )

                if st.button("Cancel Selected Booking", type="secondary"):
                    if selected_booking:
                        with st.spinner("Canceling booking..."):
                            try:
                                cancel_result = run_async_safely(
                                    cancel_booking_async(selected_booking)
                                )
                                if cancel_result.get("success"):
                                    st.success("✅ Booking canceled successfully!")
                                else:
                                    st.error(
                                        f"❌ {cancel_result.get('message', 'Cancellation failed')}"
                                    )
                            except Exception as e:
                                st.error(f"❌ Error canceling booking: {str(e)}")
            else:
                st.info("📝 No bookings found.")
        else:
            st.info("📝 No bookings available.")
            if result.get("message"):
                st.write(f"Message: {result['message']}")


def handle_statistics():
    """Handle statistics page"""
    st.header("📊 Booking Statistics")

    if st.button("📈 Load Statistics"):
        with st.spinner("Loading statistics..."):
            try:
                stats_result = run_async_safely(get_stats_async())

                if stats_result.get("success"):
                    stats = stats_result.get("statistics", {})

                    # Display key metrics
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Total Bookings", stats.get("total_bookings", 0))
                    with col2:
                        st.metric(
                            "Total Revenue", f"${stats.get('total_revenue', 0):,.2f}"
                        )
                    with col3:
                        st.metric("Active Bookings", stats.get("active_bookings", 0))
                    with col4:
                        st.metric(
                            "Canceled Bookings", stats.get("canceled_bookings", 0)
                        )

                    # Additional statistics
                    if stats.get("popular_hotels"):
                        st.subheader("🏆 Popular Hotels")
                        for hotel in stats["popular_hotels"]:
                            st.write(f"• {hotel}")

                    if stats.get("booking_trends"):
                        st.subheader("📈 Booking Trends")
                        st.json(stats["booking_trends"])

                else:
                    st.error("❌ Failed to load statistics")
                    if stats_result.get("message"):
                        st.write(f"Error: {stats_result['message']}")

            except Exception as e:
                st.error(f"❌ Error loading statistics: {str(e)}")


if __name__ == "__main__":
    main()
