# Copyright (c) 2024, VisualGraphX and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class OPSShipment(Document):
    def before_save(self):
        # Auto-generate tracking URL if carrier and tracking number are set
        if self.carrier and self.tracking_number and not self.tracking_url:
            self.tracking_url = self.get_tracking_url()

    def get_tracking_url(self):
        """Generate tracking URL based on carrier."""
        carrier_urls = {
            "UPS": f"https://www.ups.com/track?tracknum={self.tracking_number}",
            "FedEx": f"https://www.fedex.com/fedextrack/?trknbr={self.tracking_number}",
            "USPS": f"https://tools.usps.com/go/TrackConfirmAction?tLabels={self.tracking_number}",
            "DHL": f"https://www.dhl.com/us-en/home/tracking/tracking-express.html?submit=1&tracking-id={self.tracking_number}",
            "OnTrac": f"https://www.ontrac.com/tracking/?searchtype=ref&trackingres=ref&trackingnumber={self.tracking_number}",
            "GSO": f"https://www.gso.com/Tracking?TrackingNumbers={self.tracking_number}",
            "Spee-Dee": f"https://speedeedelivery.com/track/{self.tracking_number}",
        }

        # Try exact match first
        if self.carrier in carrier_urls:
            return carrier_urls[self.carrier]

        # Try partial match
        carrier_lower = self.carrier.lower()
        for name, url in carrier_urls.items():
            if name.lower() in carrier_lower or carrier_lower in name.lower():
                return url

        return None
