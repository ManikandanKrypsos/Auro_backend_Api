import 'package:flutter/material.dart';

import '../theme/color/color.dart';

class AddButton extends StatelessWidget {
    final VoidCallback onTap;
  const AddButton({
    super.key, required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 52,
        height: 52,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          color: ColorResources.primaryColor,
        ),
        child: const Icon(Icons.add, color: Colors.black, size: 26),
      ),
    );
  }
}