import 'package:flutter/material.dart';

import '../theme/color/color.dart';

class CustomAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  const CustomAppBar({super.key, required this.title});

  @override
  Widget build(BuildContext context) {
    return AppBar(
      title:  Text(
        title,
        textAlign: TextAlign.center,
        style: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: ColorResources.whiteColor,
          fontSize: 13,
          fontWeight: FontWeight.w600,
          letterSpacing: 3.5,
        ),
      ),
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}