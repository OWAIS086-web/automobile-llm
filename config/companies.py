"""
Company Configuration Module

Centralized configuration for all supported automotive companies.
Each company has its own:
- PakWheels discussion thread URL
- ChromaDB database paths
- Data file paths (.pkl, .json)
- Background image
- Available data sources (PakWheels, WhatsApp, Insights)
- WATI API credentials (optional, for WhatsApp data fetching)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class CompanyConfig:
    """Configuration for a single company"""

    # Company identification
    id: str  # Unique identifier (e.g., "haval", "kia", "toyota")
    name: str  # Display name (e.g., "Haval", "Kia", "Toyota")
    full_name: str  # Full company name (e.g., "Haval H6", "Kia Lucky Motors")

    # PakWheels configuration
    pakwheels_url: str  # Discussion thread URL
    pakwheels_thread_id: str  # Thread ID extracted from URL

    # Database paths
    chroma_pakwheels_path: str  # Vector store for PakWheels data
    chroma_whatsapp_path: Optional[str]  # Vector store for WhatsApp data (None if unavailable)
    pakwheels_blocks_file: str  # Pickle file for PakWheels conversation blocks
    whatsapp_blocks_file: Optional[str]  # Pickle file for WhatsApp conversation blocks

    # Data file paths
    pakwheels_json_pattern: str  # Pattern for PakWheels JSON files (e.g., "featured_research__{thread_title}.json")
    whatsapp_json_path: Optional[str]  # WhatsApp data JSON file path

    # UI Configuration
    background_image: str  # Background image filename (e.g., "bk.jpg", "kia.jpg")
    primary_color: str  # Primary brand color (hex)

    # Data source availability
    has_pakwheels: bool = True  # PakWheels data available
    has_whatsapp: bool = True  # WhatsApp data available
    has_insights: bool = True  # Insights mode available (uses OpenAI)

    # WATI API Configuration (optional - for WhatsApp data fetching)
    wati_api_token: Optional[str] = None  # WATI API bearer token
    wati_tenant_id: Optional[str] = None  # WATI tenant ID
    wati_api_base: str = "https://live-mt-server.wati.io"  # WATI API base URL

    # Enrichment Configuration
    variants: List[str] = None  # Vehicle variants/models for this company (e.g., ["PHEV", "HEV", "Jolion"])

    def get_available_sources(self) -> List[str]:
        """Return list of available data sources for this company"""
        sources = []
        if self.has_pakwheels:
            sources.append("pakwheels")
        if self.has_whatsapp:
            sources.append("whatsapp")
        if self.has_insights:
            sources.append("insights")
        return sources

    def is_source_available(self, source: str) -> bool:
        """Check if a specific data source is available"""
        source_lower = source.lower()
        if source_lower == "pakwheels":
            return self.has_pakwheels
        elif source_lower == "whatsapp":
            return self.has_whatsapp
        elif source_lower == "insights":
            return self.has_insights
        return False

    def has_wati_api(self) -> bool:
        """Check if company has WATI API credentials configured"""
        return self.wati_api_token is not None and self.wati_tenant_id is not None


# Company Configurations
COMPANIES: Dict[str, CompanyConfig] = {
    "haval": CompanyConfig(
        id="haval",
        name="Haval",
        full_name="Haval H6",
        pakwheels_url="https://www.pakwheels.com/forums/t/haval-h6-dedicated-discussion-owner-fan-club-thread/2198325",
        pakwheels_thread_id="haval_h6_pakwheels",
        chroma_pakwheels_path="data/chroma_pakwheels",
        chroma_whatsapp_path="data/chroma_whatsapp",
        pakwheels_blocks_file="data/pakwheels_blocks.pkl",
        whatsapp_blocks_file="data/whatsapp_blocks.pkl",
        pakwheels_json_pattern="featured_research__Haval H6 Dedicated Discussion.json",
        whatsapp_json_path="data/all_messages.json",
        background_image="bk.jpg",
        primary_color="#C8102E",  # Haval red
        has_pakwheels=True,
        has_whatsapp=True,
        has_insights=True,
        # WATI API credentials for WhatsApp data fetching
        wati_api_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImFsaS5pcWJhbEBzYXpnYXJhdXRvcy5jb20iLCJuYW1laWQiOiJhbGkuaXFiYWxAc2F6Z2FyYXV0b3MuY29tIiwiZW1haWwiOiJhbGkuaXFiYWxAc2F6Z2FyYXV0b3MuY29tIiwiYXV0aF90aW1lIjoiMDUvMjEvMjAyNSAxNDoxODo0MyIsInRlbmFudF9pZCI6IjEwNDgyMiIsImp0aSI6IjdhMDVkODUwLTQ2ZGItNGRlYS04NmNhLTIzNzUzNzA2ZDRjNCIsImRiX25hbWUiOiJtdC1wcm9kLVRlbmFudHMiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL3JvbGUiOiJBRE1JTklTVFJBVE9SIiwiZXhwIjoyNTM0MDIzMDA4MDAsImlzcyI6IkNsYXJlX0FJIiwiYXVkIjoiQ2xhcmVfQUkifQ.X01JY-X9Y-Y0NvWx02nzVys4T-_Dk-l0rlqxFAJ82dI",
        wati_tenant_id="104822",
        wati_api_base="https://live-mt-server.wati.io",
        # Vehicle variants/models for enrichment
        variants=["H6", "PHEV", "HEV", "ICE", "Jolion", "H9", "Dargo", "Unknown"],
    ),

    "kia": CompanyConfig(
        id="kia",
        name="Kia",
        full_name="Kia Lucky Motors Pakistan",
        pakwheels_url="https://www.pakwheels.com/forums/t/kia-lucky-motors-pakistan-discussion-thread-grand-carnival-rio-picanto-sportage-cerato/825345",
        pakwheels_thread_id="kia_lucky_motors_pakwheels",
        chroma_pakwheels_path="data/chroma_pakwheels_kia",
        chroma_whatsapp_path=None,  # No WhatsApp data for Kia
        pakwheels_blocks_file="data/pakwheels_blocks_kia.pkl",
        whatsapp_blocks_file=None,
        pakwheels_json_pattern="featured_research__Kia Lucky Motors Pakistan.json",
        whatsapp_json_path=None,
        background_image="kia.jpg",
        primary_color="#BB162B",  # Kia red
        has_pakwheels=True,
        has_whatsapp=False,  # No WhatsApp data available
        has_insights=True,
        # Vehicle variants/models for enrichment
        variants = [
    "Sportage",   # Available in Pakistan
    "Stonic",     # Available in Pakistan
    "Picanto",    # Available in Pakistan
    "Sorento",    # Available in Pakistan
    "Carnival",   # Available in Pakistan
    "Rio",        # Not available in Pakistan
    "Cerato",     # Not available in Pakistan
    "Unknown"     # Invalid model
]

    ),

    "toyota": CompanyConfig(
        id="toyota",
        name="Toyota",
        full_name="Toyota Indus Pakistan",
        pakwheels_url="",  # TODO: Add Toyota PakWheels URL when available
        pakwheels_thread_id="toyota_pakwheels",
        chroma_pakwheels_path="data/chroma_pakwheels_toyota",
        chroma_whatsapp_path=None,
        pakwheels_blocks_file="data/pakwheels_blocks_toyota.pkl",
        whatsapp_blocks_file=None,
        pakwheels_json_pattern="featured_research__Toyota.json",
        whatsapp_json_path=None,
        background_image="bk.jpg",  # Use default until Toyota image is added
        primary_color="#EB0A1E",  # Toyota red
        has_pakwheels=False,  # Not yet configured
        has_whatsapp=False,
        has_insights=True,
        # Vehicle variants/models for enrichment
        variants = [
    "Yaris",          # Available in Pakistan 🇵🇰 (Toyota Yaris sedan) :contentReference[oaicite:0]{index=0}
    "Corolla",        # Available in Pakistan 🇵🇰 (Toyota Corolla) :contentReference[oaicite:1]{index=1}
    "Corolla Cross",  # Available in Pakistan 🇵🇰 (Toyota Corolla Cross crossover) :contentReference[oaicite:2]{index=2}
    "Hilux",          # Available in Pakistan 🇵🇰 (Toyota Hilux pickup) :contentReference[oaicite:3]{index=3}
    "Fortuner",       # Available in Pakistan 🇵🇰 (Toyota Fortuner SUV) :contentReference[oaicite:4]{index=4}
    "Hiace",          # Available in Pakistan 🇵🇰 (Toyota Hiace van/commuter) :contentReference[oaicite:5]{index=5}
    "Coaster",        # Available in Pakistan 🇵🇰 (Toyota Coaster minibus) :contentReference[oaicite:6]{index=6}
    "Prado",          # Available in Pakistan 🇵🇰 (Toyota Prado SUV) :contentReference[oaicite:7]{index=7}
    "Land Cruiser",   # Available in Pakistan 🇵🇰 (Toyota Land Cruiser SUV) :contentReference[oaicite:8]{index=8}
    "Camry",          # Available in Pakistan 🇵🇰 (Toyota Camry sedan) :contentReference[oaicite:9]{index=9}
    "Unknown"         # Invalid / unspecified model
]

    ),
}


# Default company (Haval)
DEFAULT_COMPANY = "haval"


def get_company_config(company_id: str) -> CompanyConfig:
    """
    Get configuration for a specific company.

    Args:
        company_id: Company identifier (e.g., "haval", "kia", "toyota")

    Returns:
        CompanyConfig object

    Raises:
        ValueError: If company_id is not recognized
    """
    if company_id not in COMPANIES:
        raise ValueError(f"Unknown company: {company_id}. Available: {list(COMPANIES.keys())}")
    return COMPANIES[company_id]


def get_all_companies() -> Dict[str, CompanyConfig]:
    """Get all company configurations"""
    return COMPANIES.copy()


def get_enabled_companies() -> Dict[str, CompanyConfig]:
    """Get only companies that have at least one data source configured"""
    return {
        company_id: config
        for company_id, config in COMPANIES.items()
        if config.has_pakwheels or config.has_whatsapp
    }


def is_company_enabled(company_id: str) -> bool:
    """Check if a company is enabled (has at least one data source)"""
    try:
        config = get_company_config(company_id)
        return config.has_pakwheels or config.has_whatsapp
    except ValueError:
        return False


def get_company_display_name(company_id: str) -> str:
    """Get the display name for a company"""
    try:
        return get_company_config(company_id).name
    except ValueError:
        return "Unknown"