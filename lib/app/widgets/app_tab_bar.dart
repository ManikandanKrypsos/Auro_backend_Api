import 'package:flutter/material.dart';

import '../theme/color/color.dart';

class AppTab extends StatelessWidget {
  final String label;
  final int index;
  final int selectedTab;
  final ValueChanged<int> onTap;

  
  final double activeUnderlineWidth;

  const AppTab({
    super.key,
    required this.label,
    required this.index,
    required this.selectedTab,
    required this.onTap,
    this.activeUnderlineWidth = 140,
  });

  @override
  Widget build(BuildContext context) {
    final isSelected = selectedTab == index;

    return GestureDetector(
      onTap: () => onTap(index),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            label,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: isSelected
                  ? ColorResources.primaryColor
                  : ColorResources.liteTextColor,
              fontSize: 12,
              fontWeight: FontWeight.w600,
              letterSpacing: 2.5,
            ),
          ),
          const SizedBox(height: 6),
          AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            height: 1.5,
            width: isSelected ? activeUnderlineWidth : 0,
            color: ColorResources.primaryColor,
          ),
        ],
      ),
    );
  }
}