import 'package:flutter/material.dart';

import '../theme/color/color.dart';

class CustomAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final List<Widget>? actions;
  const CustomAppBar({super.key, required this.title, this.actions});

  @override
  Widget build(BuildContext context) {
    return AppBar(
      title: Text(
        title,
        textAlign: TextAlign.center,
        style: const TextStyle(
          fontFamily: 'CormorantGaramond',
          color: ColorResources.whiteColor,
          fontSize: 13,
          fontWeight: FontWeight.w600,
          letterSpacing: 3.5,
        ),
      ),
      actions: actions,
      centerTitle: true,
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}