/**
 * Volume conversion utilities for logarithmic volume control
 * 
 * Human perception of volume is logarithmic, not linear.
 * These utilities provide smooth volume control by mapping between:
 * - Display volume: Linear 0-100 scale shown to user
 * - Actual volume: Logarithmic 0-100 scale sent to backend
 */

/**
 * Convert display volume (linear 0-100) to actual volume (logarithmic 0-100)
 * Uses exponential mapping for perceptually uniform volume control
 * 
 * Formula: actualVolume = ((10^(displayVolume/50)) - 1) / 99 * 100
 * This creates a logarithmic curve that feels natural to human perception
 * 
 * @param displayVolume - Linear volume value (0-100) shown in UI
 * @returns Logarithmic volume value (0-100) for backend
 */
export function displayToActualVolume(displayVolume: number): number {
  // Clamp input to valid range
  const clamped = Math.max(0, Math.min(100, displayVolume));
  
  // Handle edge cases
  if (clamped === 0) return 0;
  if (clamped === 100) return 100;
  
  // Exponential mapping: (10^(displayVolume/50)) - 1) / 99 * 100
  const normalized = clamped / 100; // Convert to 0-1 range
  const exponential = (Math.pow(10, normalized * 2) - 1) / 99; // Exponential curve
  return Math.round(exponential * 100);
}

/**
 * Convert actual volume (logarithmic 0-100) to display volume (linear 0-100)
 * Inverse of displayToActualVolume
 * 
 * Formula: displayVolume = log10(actualVolume/100 * 99 + 1) / 2 * 100
 * 
 * @param actualVolume - Logarithmic volume value (0-100) from backend
 * @returns Linear volume value (0-100) for UI display
 */
export function actualToDisplayVolume(actualVolume: number): number {
  // Clamp input to valid range
  const clamped = Math.max(0, Math.min(100, actualVolume));
  
  // Handle edge cases
  if (clamped === 0) return 0;
  if (clamped === 100) return 100;
  
  // Inverse exponential mapping: log10(actualVolume/100 * 99 + 1) / 2 * 100
  const normalized = clamped / 100; // Convert to 0-1 range
  // Use natural log (ln) divided by ln(10) to compute log10
  const logarithmic = Math.log(normalized * 99 + 1) / Math.log(10) / 2; // Inverse curve
  return Math.round(logarithmic * 100);
}
