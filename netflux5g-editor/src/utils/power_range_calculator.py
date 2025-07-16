"""
Power-based Range Calculator for NetFlux5G
This module implements range calculation based on transmission power (dBm)
following the same methodology as Mininet-WiFi propagation models.
"""

import math
from typing import Dict, Any, Optional

class PowerRangeCalculator:
    """
    Calculate wireless range based on transmission power following Mininet-WiFi methodology.
    
    This class implements the same propagation models used by Mininet-WiFi to ensure
    consistent behavior between the GUI visualization and actual network simulation.
    """
    
    # Default propagation model parameters (matching Mininet-WiFi defaults)
    DEFAULT_NOISE_THRESHOLD = -91  # dBm
    DEFAULT_FREQUENCY = 2.4  # GHz
    DEFAULT_ANTENNA_GAIN = 5.0  # dBi
    DEFAULT_SYSTEM_LOSS = 1  # dB
    DEFAULT_PATH_LOSS_EXPONENT = 3  # Log-distance model exponent
    
    @staticmethod
    def calculate_range_from_power(
        txpower: float,
        frequency: float = DEFAULT_FREQUENCY,
        antenna_gain: float = DEFAULT_ANTENNA_GAIN,
        noise_threshold: float = DEFAULT_NOISE_THRESHOLD,
        system_loss: float = DEFAULT_SYSTEM_LOSS,
        path_loss_exponent: float = DEFAULT_PATH_LOSS_EXPONENT,
        model: str = "logDistance"
    ) -> float:
        """
        Calculate wireless range based on transmission power using Mininet-WiFi propagation models.
        
        Args:
            txpower: Transmission power in dBm
            frequency: Frequency in GHz
            antenna_gain: Antenna gain in dBi
            noise_threshold: Noise threshold in dBm
            system_loss: System loss in dB
            path_loss_exponent: Path loss exponent for log-distance model
            model: Propagation model ('logDistance', 'friis', 'twoRayGround')
            
        Returns:
            Range in meters
        """
        
        if model == "friis":
            return PowerRangeCalculator._calculate_friis_range(
                txpower, frequency, antenna_gain, noise_threshold, system_loss
            )
        elif model == "logDistance":
            return PowerRangeCalculator._calculate_log_distance_range(
                txpower, frequency, antenna_gain, noise_threshold, system_loss, path_loss_exponent
            )
        elif model == "twoRayGround":
            return PowerRangeCalculator._calculate_two_ray_ground_range(
                txpower, frequency, antenna_gain, noise_threshold, system_loss
            )
        else:
            # Default to log-distance model
            return PowerRangeCalculator._calculate_log_distance_range(
                txpower, frequency, antenna_gain, noise_threshold, system_loss, path_loss_exponent
            )
    
    @staticmethod
    def _calculate_friis_range(txpower: float, frequency: float, antenna_gain: float, 
                              noise_threshold: float, system_loss: float) -> float:
        """Calculate range using Friis propagation model (free space)."""
        # Convert frequency from GHz to Hz
        f_hz = frequency * 1e9
        
        # Calculate gains (tx antenna + rx antenna)
        total_gain = txpower + (antenna_gain * 2)
        
        # Speed of light
        c = 299792458.0
        
        # Calculate wavelength
        wavelength = c / f_hz
        
        # Calculate range using Friis formula
        numerator = wavelength ** 2
        denominator = (4 * math.pi) ** 2 * system_loss
        
        range_meters = math.sqrt(
            (10 ** ((total_gain - noise_threshold) / 10)) * numerator / denominator
        )
        
        return max(0.1, range_meters)
    
    @staticmethod
    def _calculate_log_distance_range(txpower: float, frequency: float, antenna_gain: float,
                                     noise_threshold: float, system_loss: float, 
                                     path_loss_exponent: float) -> float:
        """Calculate range using log-distance propagation model."""
        # Convert frequency from GHz to Hz
        f_hz = frequency * 1e9
        
        # Calculate gains (tx antenna + rx antenna)
        total_gain = txpower + (antenna_gain * 2)
        
        # Reference distance (1 meter)
        ref_d = 1.0
        
        # Calculate path loss at reference distance (Friis formula)
        c = 299792458.0
        wavelength = c / f_hz
        pl_ref = 10 * math.log10(((4 * math.pi * ref_d) ** 2 * system_loss) / wavelength ** 2)
        
        # Calculate range using log-distance formula
        numerator = total_gain - noise_threshold - pl_ref
        denominator = 10 * path_loss_exponent
        
        range_meters = math.pow(10, numerator / denominator) * ref_d
        
        return max(0.1, range_meters)
    
    @staticmethod
    def _calculate_two_ray_ground_range(txpower: float, frequency: float, antenna_gain: float,
                                       noise_threshold: float, system_loss: float, 
                                       antenna_height: float = 1.5) -> float:
        """Calculate range using two-ray ground propagation model."""
        # This is a simplified version - actual implementation would need more parameters
        # For now, fall back to log-distance model
        return PowerRangeCalculator._calculate_log_distance_range(
            txpower, frequency, antenna_gain, noise_threshold, system_loss, 3.5
        )
    
    @staticmethod
    def get_component_range(component_type: str, properties: Dict[str, Any]) -> float:
        """
        Get the wireless range for a component based on its power configuration.
        
        Args:
            component_type: Type of component ('AP', 'GNB', 'UE', 'STA')
            properties: Component properties dictionary
            
        Returns:
            Range in meters
        """
        
        # Get power value from properties
        power_fields = PowerRangeCalculator._get_power_fields(component_type)
        txpower = None
        
        for field in power_fields:
            if properties.get(field):
                try:
                    txpower = float(str(properties[field]).strip())
                    if txpower > 0:
                        break
                except (ValueError, TypeError):
                    continue
        
        # Use default power if not specified
        if txpower is None:
            txpower = PowerRangeCalculator._get_default_power(component_type)
        
        # Get frequency for the component
        frequency = PowerRangeCalculator._get_component_frequency(component_type, properties)
        
        # Calculate range based on power
        return PowerRangeCalculator.calculate_range_from_power(
            txpower=txpower,
            frequency=frequency,
            model="logDistance"  # Use log-distance as default (matches Mininet-WiFi)
        )
    
    @staticmethod
    def _get_power_fields(component_type: str) -> list:
        """Get the property field names that contain power values for a component type."""
        if component_type == "AP":
            return ["AP_Power", "AP_TxPower", "txpower", "power"]
        elif component_type == "GNB":
            return ["GNB_Power", "GNB_TxPower", "txpower", "power"]
        elif component_type == "UE":
            return ["UE_Power", "UE_TxPower", "txpower", "power"]
        elif component_type == "STA":
            return ["STA_Power", "STA_TxPower", "txpower", "power"]
        else:
            return ["txpower", "power"]
    
    @staticmethod
    def _get_default_power(component_type: str) -> float:
        """Get default transmission power for a component type."""
        defaults = {
            "AP": 20.0,    # dBm - typical for WiFi access points
            "GNB": 30.0,   # dBm - typical for 5G base stations
            "UE": 20.0,    # dBm - typical for mobile devices
            "STA": 20.0,   # dBm - typical for WiFi stations
        }
        return defaults.get(component_type, 20.0)
    
    @staticmethod
    def _get_component_frequency(component_type: str, properties: Dict[str, Any]) -> float:
        """Get operating frequency for a component type."""
        
        # Check if frequency is explicitly set in properties
        freq_fields = []
        if component_type == "AP":
            freq_fields = ["AP_Frequency", "frequency", "freq"]
        elif component_type == "GNB":
            freq_fields = ["GNB_Frequency", "frequency", "freq"]
        elif component_type in ["UE", "STA"]:
            freq_fields = ["frequency", "freq"]
        
        for field in freq_fields:
            if properties.get(field):
                try:
                    freq = float(str(properties[field]).strip())
                    if freq > 0:
                        return freq
                except (ValueError, TypeError):
                    continue
        
        # Default frequencies based on component type
        if component_type == "AP":
            # WiFi 2.4GHz (channel 1-11) or 5GHz (channel 36+)
            channel = properties.get("AP_Channel", "1")
            try:
                ch = int(channel)
                if ch >= 36:
                    return 5.0  # 5GHz
                else:
                    return 2.4  # 2.4GHz
            except (ValueError, TypeError):
                return 2.4
        elif component_type == "GNB":
            # 5G NR frequencies - default to 3.5GHz (common mid-band)
            return 3.5
        else:
            # Default to 2.4GHz for stations/UEs
            return 2.4
    
    @staticmethod
    def calculate_power_from_range(
        target_range: float,
        frequency: float = DEFAULT_FREQUENCY,
        antenna_gain: float = DEFAULT_ANTENNA_GAIN,
        noise_threshold: float = DEFAULT_NOISE_THRESHOLD,
        system_loss: float = DEFAULT_SYSTEM_LOSS,
        path_loss_exponent: float = DEFAULT_PATH_LOSS_EXPONENT,
        model: str = "logDistance"
    ) -> float:
        """
        Calculate required transmission power to achieve a target range.
        
        Args:
            target_range: Desired range in meters
            frequency: Frequency in GHz
            antenna_gain: Antenna gain in dBi
            noise_threshold: Noise threshold in dBm
            system_loss: System loss in dB
            path_loss_exponent: Path loss exponent for log-distance model
            model: Propagation model ('logDistance', 'friis', 'twoRayGround')
            
        Returns:
            Required transmission power in dBm
        """
        
        if model == "logDistance":
            return PowerRangeCalculator._calculate_log_distance_power(
                target_range, frequency, antenna_gain, noise_threshold, system_loss, path_loss_exponent
            )
        elif model == "friis":
            return PowerRangeCalculator._calculate_friis_power(
                target_range, frequency, antenna_gain, noise_threshold, system_loss
            )
        else:
            # Default to log-distance model
            return PowerRangeCalculator._calculate_log_distance_power(
                target_range, frequency, antenna_gain, noise_threshold, system_loss, path_loss_exponent
            )
    
    @staticmethod
    def _calculate_log_distance_power(target_range: float, frequency: float, antenna_gain: float,
                                     noise_threshold: float, system_loss: float, 
                                     path_loss_exponent: float) -> float:
        """Calculate power required for target range using log-distance model."""
        # Convert frequency from GHz to Hz
        f_hz = frequency * 1e9
        
        # Reference distance (1 meter)
        ref_d = 1.0
        
        # Calculate path loss at reference distance
        c = 299792458.0
        wavelength = c / f_hz
        pl_ref = 10 * math.log10(((4 * math.pi * ref_d) ** 2 * system_loss) / wavelength ** 2)
        
        # Calculate path loss at target distance
        pl_target = 10 * path_loss_exponent * math.log10(target_range / ref_d)
        
        # Calculate required power
        # total_gain = txpower + (antenna_gain * 2)
        # received_power = total_gain - pl_ref - pl_target
        # received_power >= noise_threshold
        
        required_power = noise_threshold + pl_ref + pl_target - (antenna_gain * 2)
        
        return max(1.0, required_power)  # Minimum 1 dBm
    
    @staticmethod
    def _calculate_friis_power(target_range: float, frequency: float, antenna_gain: float,
                              noise_threshold: float, system_loss: float) -> float:
        """Calculate power required for target range using Friis model."""
        # Convert frequency from GHz to Hz
        f_hz = frequency * 1e9
        
        # Speed of light
        c = 299792458.0
        
        # Calculate wavelength
        wavelength = c / f_hz
        
        # Calculate required power using Friis formula
        path_loss = 10 * math.log10(((4 * math.pi * target_range) ** 2 * system_loss) / wavelength ** 2)
        
        required_power = noise_threshold + path_loss - (antenna_gain * 2)
        
        return max(1.0, required_power)  # Minimum 1 dBm
