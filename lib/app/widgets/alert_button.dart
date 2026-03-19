
import 'package:flutter/material.dart';

import '../theme/color/color.dart';

class AlertButton extends StatelessWidget {
  final VoidCallback onTap;
  final String text;
  const AlertButton({
    super.key, required this.onTap, required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton(
        onPressed: onTap,
       
        style: OutlinedButton.styleFrom(
          side: BorderSide(
            color: ColorResources.negativeColor.withOpacity(0.6),
            width: 0.8,
          ),
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(
              10,
            ), // rectangle with soft corners
          ),
        ),
        child: Text(
          text,
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.negativeColor.withOpacity(0.8),
            fontSize: 13,
            fontWeight: FontWeight.w600,
            letterSpacing: 3.0,
          ),
        ),
      ),
    );
  }
}