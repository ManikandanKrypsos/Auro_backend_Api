import 'package:flutter/material.dart';

import '../theme/color/color.dart';

class SecondaryButton extends StatelessWidget {
  final VoidCallback onTap;
  final String title;
  final IconData? icon;

  final double height;

  const SecondaryButton({
    super.key,
    required this.onTap,
    required this.title,
    this.icon,
    this.height = 46,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: height,
        decoration: BoxDecoration(
          color: const Color(0xFF1E1E1E),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: ColorResources.borderColor,
            width: 0.5,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (icon != null) ...[
              Icon(
                icon,
                size: 14,
                color: ColorResources.primaryColor.withOpacity(0.85),
              ),
              const SizedBox(width: 8),
            ],
            Text(
              title,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor.withOpacity(0.85),
                fontSize: 11,
                fontWeight: FontWeight.w600,
                letterSpacing: 2,
              ),
            ),
          ],
        ),
      ),
    );
  }
}