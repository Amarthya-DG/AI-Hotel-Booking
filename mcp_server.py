"""
Hotel Booking MCP Server with dummy data
"""

import json
import uuid
from datetime import datetime
from typing import List

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

# Initialize the MCP server
mcp = FastMCP("HotelBooking")


# Dummy data models
class Hotel(BaseModel):
    id: str
    name: str
    location: str
    rating: float
    amenities: List[str]
    price_per_night: float
    available_rooms: int
    description: str


class Room(BaseModel):
    id: str
    hotel_id: str
    room_type: str
    capacity: int
    price_per_night: float
    amenities: List[str]
    available: bool


class Booking(BaseModel):
    id: str
    hotel_id: str
    room_id: str
    guest_name: str
    guest_email: str
    check_in: str
    check_out: str
    total_price: float
    status: str


# Dummy data storage
HOTELS: List[Hotel] = [
    Hotel(
        id="hotel_1",
        name="Grand Plaza Hotel",
        location="New York, NY",
        rating=4.5,
        amenities=["WiFi", "Pool", "Gym", "Restaurant", "Spa"],
        price_per_night=250.0,
        available_rooms=15,
        description="Luxurious hotel in the heart of Manhattan with stunning city views",
    ),
    Hotel(
        id="hotel_2",
        name="Seaside Resort",
        location="Miami, FL",
        rating=4.2,
        amenities=["WiFi", "Beach Access", "Pool", "Restaurant", "Bar"],
        price_per_night=180.0,
        available_rooms=8,
        description="Beautiful beachfront resort with direct ocean access",
    ),
    Hotel(
        id="hotel_3",
        name="Mountain View Lodge",
        location="Denver, CO",
        rating=4.0,
        amenities=["WiFi", "Fireplace", "Hiking Trails", "Restaurant"],
        price_per_night=120.0,
        available_rooms=12,
        description="Cozy mountain lodge perfect for nature lovers",
    ),
    Hotel(
        id="hotel_4",
        name="Business Center Hotel",
        location="Chicago, IL",
        rating=4.3,
        amenities=["WiFi", "Business Center", "Gym", "Conference Rooms"],
        price_per_night=200.0,
        available_rooms=20,
        description="Modern business hotel ideal for corporate travelers",
    ),
    Hotel(
        id="hotel_5",
        name="Historic Inn",
        location="Boston, MA",
        rating=4.1,
        amenities=["WiFi", "Historic Charm", "Restaurant", "Library"],
        price_per_night=160.0,
        available_rooms=6,
        description="Charming historic inn with old-world elegance",
    ),
    Hotel(
        id="hotel_6",
        name="Ocean View Resort",
        location="San Francisco, CA",
        rating=4.4,
        amenities=["WiFi", "Beach Access", "Pool", "Restaurant", "Spa"],
        price_per_night=190.0,
        available_rooms=10,
        description="Beautiful oceanfront resort near Golden Gate Bridge with beach access",
    ),
    Hotel(
        id="hotel_7",
        name="Bay Side Hotel",
        location="San Francisco, CA",
        rating=4.2,
        amenities=["WiFi", "Bay Views", "Restaurant", "Gym"],
        price_per_night=170.0,
        available_rooms=8,
        description="Modern hotel with stunning bay views, walking distance to beaches",
    ),
    Hotel(
        id="hotel_8",
        name="Coastal Inn",
        location="San Francisco, CA",
        rating=4.0,
        amenities=["WiFi", "Beach Nearby", "Restaurant", "Parking"],
        price_per_night=150.0,
        available_rooms=12,
        description="Comfortable inn just 2 blocks from the beach, perfect for budget travelers",
    ),
    Hotel(
        id="hotel_9",
        name="Budget Beach Motel",
        location="San Francisco, CA",
        rating=3.5,
        amenities=["WiFi", "Beach Access", "Parking"],
        price_per_night=85.0,
        available_rooms=15,
        description="Simple, clean motel with direct beach access at unbeatable prices",
    ),
    Hotel(
        id="hotel_10",
        name="Surfer's Paradise Hostel",
        location="San Francisco, CA",
        rating=3.8,
        amenities=["WiFi", "Beach Nearby", "Shared Kitchen", "Lounge"],
        price_per_night=75.0,
        available_rooms=20,
        description="Friendly hostel just steps from the beach, perfect for budget travelers",
    ),
    Hotel(
        id="hotel_11",
        name="Ocean Breeze Inn",
        location="San Francisco, CA",
        rating=3.7,
        amenities=["WiFi", "Beach View", "Restaurant"],
        price_per_night=95.0,
        available_rooms=10,
        description="Cozy inn with ocean views and easy beach access",
    ),
]

ROOMS: List[Room] = [
    # Grand Plaza Hotel rooms
    Room(
        id="room_1_1",
        hotel_id="hotel_1",
        room_type="Standard",
        capacity=2,
        price_per_night=250.0,
        amenities=["WiFi", "TV", "AC"],
        available=True,
    ),
    Room(
        id="room_1_2",
        hotel_id="hotel_1",
        room_type="Deluxe",
        capacity=3,
        price_per_night=350.0,
        amenities=["WiFi", "TV", "AC", "Mini Bar"],
        available=True,
    ),
    Room(
        id="room_1_3",
        hotel_id="hotel_1",
        room_type="Suite",
        capacity=4,
        price_per_night=500.0,
        amenities=["WiFi", "TV", "AC", "Mini Bar", "Living Room"],
        available=True,
    ),
    # Seaside Resort rooms
    Room(
        id="room_2_1",
        hotel_id="hotel_2",
        room_type="Ocean View",
        capacity=2,
        price_per_night=180.0,
        amenities=["WiFi", "TV", "Balcony"],
        available=True,
    ),
    Room(
        id="room_2_2",
        hotel_id="hotel_2",
        room_type="Beach Suite",
        capacity=4,
        price_per_night=280.0,
        amenities=["WiFi", "TV", "Balcony", "Kitchenette"],
        available=True,
    ),
    # Mountain View Lodge rooms
    Room(
        id="room_3_1",
        hotel_id="hotel_3",
        room_type="Cabin",
        capacity=2,
        price_per_night=120.0,
        amenities=["WiFi", "Fireplace"],
        available=True,
    ),
    Room(
        id="room_3_2",
        hotel_id="hotel_3",
        room_type="Family Cabin",
        capacity=6,
        price_per_night=200.0,
        amenities=["WiFi", "Fireplace", "Kitchenette"],
        available=True,
    ),
    # Business Center Hotel rooms
    Room(
        id="room_4_1",
        hotel_id="hotel_4",
        room_type="Business",
        capacity=1,
        price_per_night=200.0,
        amenities=["WiFi", "Desk", "TV"],
        available=True,
    ),
    Room(
        id="room_4_2",
        hotel_id="hotel_4",
        room_type="Executive",
        capacity=2,
        price_per_night=280.0,
        amenities=["WiFi", "Desk", "TV", "Meeting Area"],
        available=True,
    ),
    # Historic Inn rooms
    Room(
        id="room_5_1",
        hotel_id="hotel_5",
        room_type="Classic",
        capacity=2,
        price_per_night=160.0,
        amenities=["WiFi", "Antique Furniture"],
        available=True,
    ),
    # Ocean View Resort (SF) rooms
    Room(
        id="room_6_1",
        hotel_id="hotel_6",
        room_type="Ocean View",
        capacity=2,
        price_per_night=190.0,
        amenities=["WiFi", "TV", "Ocean View", "Balcony"],
        available=True,
    ),
    Room(
        id="room_6_2",
        hotel_id="hotel_6",
        room_type="Beach Suite",
        capacity=4,
        price_per_night=290.0,
        amenities=["WiFi", "TV", "Ocean View", "Balcony", "Kitchenette"],
        available=True,
    ),
    # Bay Side Hotel (SF) rooms
    Room(
        id="room_7_1",
        hotel_id="hotel_7",
        room_type="Bay View",
        capacity=2,
        price_per_night=170.0,
        amenities=["WiFi", "TV", "Bay View"],
        available=True,
    ),
    Room(
        id="room_7_2",
        hotel_id="hotel_7",
        room_type="Premium Bay",
        capacity=3,
        price_per_night=220.0,
        amenities=["WiFi", "TV", "Bay View", "Mini Bar"],
        available=True,
    ),
    # Coastal Inn (SF) rooms
    Room(
        id="room_8_1",
        hotel_id="hotel_8",
        room_type="Standard",
        capacity=2,
        price_per_night=150.0,
        amenities=["WiFi", "TV"],
        available=True,
    ),
    Room(
        id="room_8_2",
        hotel_id="hotel_8",
        room_type="Beach Side",
        capacity=4,
        price_per_night=180.0,
        amenities=["WiFi", "TV", "Beach View"],
        available=True,
    ),
    # Budget Beach Motel (SF) rooms
    Room(
        id="room_9_1",
        hotel_id="hotel_9",
        room_type="Economy",
        capacity=2,
        price_per_night=85.0,
        amenities=["WiFi", "TV"],
        available=True,
    ),
    Room(
        id="room_9_2",
        hotel_id="hotel_9",
        room_type="Beachfront",
        capacity=3,
        price_per_night=95.0,
        amenities=["WiFi", "TV", "Beach View"],
        available=True,
    ),
    # Surfer's Paradise Hostel (SF) rooms
    Room(
        id="room_10_1",
        hotel_id="hotel_10",
        room_type="Dorm Bed",
        capacity=1,
        price_per_night=75.0,
        amenities=["WiFi", "Shared Bathroom"],
        available=True,
    ),
    Room(
        id="room_10_2",
        hotel_id="hotel_10",
        room_type="Private Room",
        capacity=2,
        price_per_night=90.0,
        amenities=["WiFi", "Private Bathroom"],
        available=True,
    ),
    # Ocean Breeze Inn (SF) rooms
    Room(
        id="room_11_1",
        hotel_id="hotel_11",
        room_type="Standard",
        capacity=2,
        price_per_night=95.0,
        amenities=["WiFi", "TV", "Ocean View"],
        available=True,
    ),
    Room(
        id="room_11_2",
        hotel_id="hotel_11",
        room_type="Deluxe Ocean",
        capacity=3,
        price_per_night=110.0,
        amenities=["WiFi", "TV", "Ocean View", "Balcony"],
        available=True,
    ),
]

BOOKINGS: List[Booking] = [
    Booking(
        id="booking_001",
        hotel_id="hotel_1",
        room_id="room_1_1",
        guest_name="John Smith",
        guest_email="john.smith@email.com",
        check_in="2024-12-20",
        check_out="2024-12-23",
        total_price=750.0,
        status="confirmed",
    ),
    Booking(
        id="booking_002",
        hotel_id="hotel_2",
        room_id="room_2_1",
        guest_name="Sarah Johnson",
        guest_email="sarah.j@email.com",
        check_in="2024-12-25",
        check_out="2024-12-27",
        total_price=360.0,
        status="confirmed",
    ),
    Booking(
        id="booking_003",
        hotel_id="hotel_6",
        room_id="room_6_1",
        guest_name="Mike Davis",
        guest_email="mike.davis@email.com",
        check_in="2025-01-15",
        check_out="2025-01-18",
        total_price=570.0,
        status="confirmed",
    ),
    Booking(
        id="booking_004",
        hotel_id="hotel_7",
        room_id="room_7_1",
        guest_name="Emma Wilson",
        guest_email="emma.wilson@email.com",
        check_in="2025-02-10",
        check_out="2025-02-12",
        total_price=340.0,
        status="pending",
    ),
    Booking(
        id="booking_005",
        hotel_id="hotel_9",
        room_id="room_9_1",
        guest_name="David Brown",
        guest_email="david.brown@email.com",
        check_in="2024-12-30",
        check_out="2025-01-02",
        total_price=255.0,
        status="confirmed",
    ),
]


@mcp.tool()
def search_hotels(
    location: str = "",
    min_rating: float = 0.0,
    max_price: float = 1000.0,
    amenities: str = "",
) -> str:
    """
    Search for hotels based on criteria.

    Args:
        location: Location to search in (city name, state, etc.)
        min_rating: Minimum hotel rating (0.0 to 5.0)
        max_price: Maximum price per night
        amenities: Comma-separated list of desired amenities

    Returns:
        JSON string with matching hotels
    """
    results = []

    # Parse amenities
    amenity_list = [a.strip().lower() for a in amenities.split(",") if a.strip()]

    for hotel in HOTELS:
        # Filter by location (more flexible matching)
        if location and location.strip():
            location_lower = location.lower().strip()
            hotel_location_lower = hotel.location.lower()

            # Check if location is contained in hotel location or vice versa
            if not (
                location_lower in hotel_location_lower
                or any(
                    loc_part.strip() in hotel_location_lower
                    for loc_part in location_lower.split(",")
                    if loc_part.strip()
                )
                or hotel_location_lower.split(",")[0].strip() in location_lower
            ):
                continue

        # Filter by rating
        if hotel.rating < min_rating:
            continue

        # Filter by price
        if hotel.price_per_night > max_price:
            continue

        # Filter by amenities
        if amenity_list:
            hotel_amenities_lower = [a.lower() for a in hotel.amenities]
            amenity_match = False
            for desired_amenity in amenity_list:
                # Check for partial matches (e.g., "beach" matches "Beach Access")
                if any(
                    desired_amenity in hotel_amenity
                    for hotel_amenity in hotel_amenities_lower
                ):
                    amenity_match = True
                    break
            if not amenity_match:
                continue

        results.append(hotel.model_dump())

    return json.dumps({"hotels": results, "count": len(results)})


@mcp.tool()
def get_hotel_details(hotel_id: str) -> str:
    """
    Get detailed information about a specific hotel including available rooms.

    Args:
        hotel_id: The ID of the hotel

    Returns:
        JSON string with hotel details and available rooms
    """
    # Find the hotel
    hotel = next((h for h in HOTELS if h.id == hotel_id), None)
    if not hotel:
        return json.dumps({"error": "Hotel not found"})

    # Get available rooms for this hotel
    available_rooms = [
        room.model_dump()
        for room in ROOMS
        if room.hotel_id == hotel_id and room.available
    ]

    result = {"hotel": hotel.model_dump(), "available_rooms": available_rooms}

    return json.dumps(result)


@mcp.tool()
def check_availability(
    hotel_id: str, check_in: str, check_out: str, guests: int = 2
) -> str:
    """
    Check room availability for specific dates.

    Args:
        hotel_id: The ID of the hotel
        check_in: Check-in date (YYYY-MM-DD format)
        check_out: Check-out date (YYYY-MM-DD format)
        guests: Number of guests (default: 2)

    Returns:
        JSON string with available rooms for the specified dates
    """
    # Find the hotel
    hotel = next((h for h in HOTELS if h.id == hotel_id), None)
    if not hotel:
        return json.dumps({"error": "Hotel not found"})

    # Get rooms for this hotel that can accommodate the guests
    available_rooms = []

    for room in ROOMS:
        if room.hotel_id == hotel_id and room.available and room.capacity >= guests:
            # Check if room has conflicting bookings for the requested dates
            conflicting_bookings = [
                b
                for b in BOOKINGS
                if b.room_id == room.id
                and b.status in ["confirmed", "pending"]
                and not (check_out <= b.check_in or check_in >= b.check_out)
            ]

            if not conflicting_bookings:
                available_rooms.append(room.model_dump())

    suitable_rooms = available_rooms

    result = {
        "hotel_id": hotel_id,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "available_rooms": suitable_rooms,
    }

    return json.dumps(result)


@mcp.tool()
def book_hotel(
    hotel_id: str,
    room_id: str,
    guest_name: str,
    guest_email: str,
    check_in: str,
    check_out: str,
) -> str:
    """
    Book a hotel room.

    Args:
        hotel_id: The ID of the hotel
        room_id: The ID of the room to book
        guest_name: Guest's full name
        guest_email: Guest's email address
        check_in: Check-in date (YYYY-MM-DD format)
        check_out: Check-out date (YYYY-MM-DD format)

    Returns:
        JSON string with booking confirmation details
    """
    # Find the hotel and room
    hotel = next((h for h in HOTELS if h.id == hotel_id), None)
    room = next((r for r in ROOMS if r.id == room_id and r.hotel_id == hotel_id), None)

    if not hotel:
        return json.dumps({"error": "Hotel not found"})

    if not room:
        return json.dumps({"error": "Room not found"})

    if not room.available:
        return json.dumps({"error": "Room is not available"})

    # Calculate total price
    try:
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
        nights = (check_out_date - check_in_date).days

        if nights <= 0:
            return json.dumps({"error": "Invalid date range"})

        total_price = room.price_per_night * nights
    except ValueError:
        return json.dumps({"error": "Invalid date format. Use YYYY-MM-DD"})

    # Check for conflicting bookings (more realistic availability)
    conflicting_bookings = [
        b
        for b in BOOKINGS
        if b.room_id == room_id
        and b.status in ["confirmed", "pending"]
        and not (check_out <= b.check_in or check_in >= b.check_out)
    ]

    if conflicting_bookings:
        return json.dumps(
            {
                "error": "Room is not available for these dates due to existing bookings",
                "conflicting_dates": [
                    f"{b.check_in} to {b.check_out}" for b in conflicting_bookings
                ],
            }
        )

    # Create booking
    booking_id = str(uuid.uuid4())
    booking = Booking(
        id=booking_id,
        hotel_id=hotel_id,
        room_id=room_id,
        guest_name=guest_name,
        guest_email=guest_email,
        check_in=check_in,
        check_out=check_out,
        total_price=total_price,
        status="confirmed",
    )

    # Add to bookings
    BOOKINGS.append(booking)

    result = {
        "booking_confirmation": booking.model_dump(),
        "hotel": hotel.model_dump(),
        "room": room.model_dump(),
        "nights": nights,
        "message": f"Booking confirmed! Your reservation ID is {booking_id}",
    }

    return json.dumps(result)


@mcp.tool()
def get_booking_details(booking_id: str) -> str:
    """
    Get details of an existing booking.

    Args:
        booking_id: The booking ID

    Returns:
        JSON string with booking details
    """
    booking = next((b for b in BOOKINGS if b.id == booking_id), None)
    if not booking:
        return json.dumps({"error": "Booking not found"})

    # Get hotel and room details
    hotel = next((h for h in HOTELS if h.id == booking.hotel_id), None)
    room = next((r for r in ROOMS if r.id == booking.room_id), None)

    result = {
        "booking": booking.model_dump(),
        "hotel": hotel.model_dump() if hotel else None,
        "room": room.model_dump() if room else None,
    }

    return json.dumps(result)


@mcp.tool()
def cancel_booking(booking_id: str) -> str:
    """
    Cancel an existing booking.

    Args:
        booking_id: The booking ID to cancel

    Returns:
        JSON string with cancellation confirmation
    """
    booking = next((b for b in BOOKINGS if b.id == booking_id), None)
    if not booking:
        return json.dumps({"error": "Booking not found"})

    if booking.status == "cancelled":
        return json.dumps({"error": "Booking is already cancelled"})

    # Update booking status
    old_status = booking.status
    booking.status = "cancelled"

    # Make the room available again
    room = next((r for r in ROOMS if r.id == booking.room_id), None)
    if room:
        room.available = True

    result = {
        "booking_id": booking_id,
        "previous_status": old_status,
        "new_status": "cancelled",
        "message": f"Booking {booking_id} has been successfully cancelled",
        "refund_amount": booking.total_price,
    }

    return json.dumps(result)


@mcp.tool()
def list_all_bookings() -> str:
    """
    List all current bookings.

    Returns:
        JSON string with all bookings
    """
    return json.dumps({"bookings": [booking.model_dump() for booking in BOOKINGS]})


@mcp.tool()
def get_booking_statistics() -> str:
    """
    Get summary statistics about all bookings.

    Returns:
        JSON string with booking statistics
    """
    total_bookings = len(BOOKINGS)
    confirmed_bookings = len([b for b in BOOKINGS if b.status == "confirmed"])
    pending_bookings = len([b for b in BOOKINGS if b.status == "pending"])
    cancelled_bookings = len([b for b in BOOKINGS if b.status == "cancelled"])

    total_revenue = sum(b.total_price for b in BOOKINGS if b.status == "confirmed")

    # Most popular hotels
    hotel_booking_counts = {}
    for booking in BOOKINGS:
        if booking.status in ["confirmed", "pending"]:
            hotel_booking_counts[booking.hotel_id] = (
                hotel_booking_counts.get(booking.hotel_id, 0) + 1
            )

    popular_hotels = []
    for hotel_id, count in sorted(
        hotel_booking_counts.items(), key=lambda x: x[1], reverse=True
    ):
        hotel = next((h for h in HOTELS if h.id == hotel_id), None)
        if hotel:
            popular_hotels.append({"hotel_name": hotel.name, "booking_count": count})

    result = {
        "total_bookings": total_bookings,
        "confirmed_bookings": confirmed_bookings,
        "pending_bookings": pending_bookings,
        "cancelled_bookings": cancelled_bookings,
        "total_revenue": total_revenue,
        "most_popular_hotels": popular_hotels[:5],  # Top 5
    }

    return json.dumps(result)


if __name__ == "__main__":
    print("Starting Hotel Booking MCP Server...")
    mcp.run(transport="stdio")
