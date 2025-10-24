# Domain Availability Checker Demo

This demo showcases how ACE learns optimal domain search strategies across different domain checking websites.

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install ace-framework[demos]
   ```

2. **Set API key**:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

3. **Run baseline** (fixed strategy):
   ```bash
   python session1_baseline.py
   ```

4. **Run ACE-enhanced** (learns optimal site selection):
   ```bash
   python session2_with_ace.py
   ```

## What It Demonstrates

- **Baseline**: Uses a fixed site selection strategy
- **ACE Enhancement**: Learns which domain checking sites work best based on performance
- **Results**: Improved site selection, faster domain availability checks, better reliability

## Files

- `session1_baseline.py` - Baseline implementation with fixed strategy
- `session2_with_ace.py` - ACE-enhanced version with learning capabilities

For detailed documentation, see the main [ACE Framework README](../../README.md).