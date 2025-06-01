"""
Hourglass Statistics Tracker

This module tracks usage statistics for the ASCII hourglass timer,
storing information about how long the timer has been running
across different time periods.
"""

import json
import os
import time
import datetime
from collections import defaultdict

# File to store statistics
STATS_FILE = "hourglass_stats.json"

class HourglassStats:
    """Tracks and manages hourglass usage statistics."""
    
    def __init__(self):
        self.stats = {
            'total_seconds': 0,
            'by_day': {},
            'by_week': {},
            'by_month': {},
            'by_year': {},
            'last_updated': 0
        }
        self.load_stats()
    
    def load_stats(self):
        """Load existing statistics from file."""
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r') as f:
                    data = json.load(f)
                    self.stats = data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading statistics: {e}")
    
    def save_stats(self):
        """Save statistics to file."""
        try:
            with open(STATS_FILE, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except IOError as e:
            print(f"Error saving statistics: {e}")
    
    def update_stats(self, seconds):
        """Update statistics with new usage time.
        
        Args:
            seconds: Number of seconds the hourglass was used
        """
        if seconds <= 0:
            return
            
        # Update total seconds
        self.stats['total_seconds'] += seconds
        
        # Get the date info
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        week_str = f"{now.year}-W{now.strftime('%U')}"
        month_str = now.strftime("%Y-%m")
        year_str = str(now.year)
        
        # Update daily stats
        if date_str not in self.stats['by_day']:
            self.stats['by_day'][date_str] = 0
        self.stats['by_day'][date_str] += seconds
        
        # Update weekly stats
        if week_str not in self.stats['by_week']:
            self.stats['by_week'][week_str] = 0
        self.stats['by_week'][week_str] += seconds
        
        # Update monthly stats
        if month_str not in self.stats['by_month']:
            self.stats['by_month'][month_str] = 0
        self.stats['by_month'][month_str] += seconds
        
        # Update yearly stats
        if year_str not in self.stats['by_year']:
            self.stats['by_year'][year_str] = 0
        self.stats['by_year'][year_str] += seconds
        
        # Update timestamp
        self.stats['last_updated'] = time.time()
        
        # Save updated stats
        self.save_stats()
    
    def get_summary(self):
        """Get a human-readable summary of usage statistics.
        
        Returns:
            A formatted string with usage statistics
        """
        hours_total = self.stats['total_seconds'] / 3600
        
        # Get today's stats
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        week_str = f"{now.year}-W{now.strftime('%U')}"
        month_str = now.strftime("%Y-%m")
        year_str = str(now.year)
        
        hours_today = self.stats['by_day'].get(date_str, 0) / 3600
        hours_this_week = self.stats['by_week'].get(week_str, 0) / 3600
        hours_this_month = self.stats['by_month'].get(month_str, 0) / 3600
        hours_this_year = self.stats['by_year'].get(year_str, 0) / 3600
        
        summary = [
            "=== Hourglass Usage Statistics ===",
            f"Total time:       {hours_total:.2f} hours",
            f"Today:            {hours_today:.2f} hours",
            f"This week:        {hours_this_week:.2f} hours",
            f"This month:       {hours_this_month:.2f} hours",
            f"This year:        {hours_this_year:.2f} hours"
        ]
        
        return "\n".join(summary)

def show_stats():
    """Display the current usage statistics."""
    stats = HourglassStats()
    print(stats.get_summary())

if __name__ == "__main__":
    show_stats() 