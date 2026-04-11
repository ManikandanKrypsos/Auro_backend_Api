import 'package:aura/app/theme/color/color.dart';
import 'package:flutter/material.dart';

import '../page/admin/admin_main_screen/repository/model';

class AppBottomNavBar extends StatelessWidget {
  const AppBottomNavBar({
    super.key,
    required this.items,
    required this.activeIndex,
    this.width
  });

  final List<NavItemData> items;
  final int activeIndex;
final double?width;
  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF111111),
        border: Border(
          top: BorderSide(color: Color(0xFF222222), width: 0.5),
        ),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: List.generate(items.length, (index) {
              final item = items[index];
              return _NavItem(
                icon: item.icon,
                label: item.label,
                isActive: activeIndex == index,
                onTap: item.onTap,
width: width,
              );
            }),
          ),
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  const _NavItem({

    required this.icon,
    required this.label,
    required this.isActive,
    required this.onTap,
this.width=65
  });

  final IconData icon;
  final String label;
  final bool isActive;
  final VoidCallback onTap;
final double?width;

  static const _inactive = ColorResources.liteTextColor;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: SizedBox(
        width: width,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            AnimatedSwitcher(
              duration: const Duration(milliseconds: 200),
              child: Icon(
                icon,
                key: ValueKey(isActive),
                size: 22,
                color: isActive ? ColorResources.primaryColor : _inactive,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                fontSize: 9,
                letterSpacing: 1.5,
                color: isActive ? ColorResources.primaryColor : _inactive,
                fontWeight: FontWeight.w400,
              ),
            ),
            const SizedBox(height: 4),
            AnimatedContainer(
              duration: const Duration(milliseconds: 250),
              curve: Curves.easeOut,
              width: isActive ? 4 : 0,
              height: isActive ? 4 : 0,
              decoration: const BoxDecoration(
                color: ColorResources.primaryColor,
                shape: BoxShape.circle,
              ),
            ),
          ],
        ),
      ),
    );
  }
}