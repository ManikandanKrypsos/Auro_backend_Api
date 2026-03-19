import 'package:aura/app/theme/color/color.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../cubit/nav_cubit.dart';

class AdminBottomNavBar extends StatelessWidget {
  const AdminBottomNavBar({super.key});


  static const _items = [
    (tab: NavTab.dashboard, label: 'DASH',     icon: Icons.grid_view_rounded),
    (tab: NavTab.staff,     label: 'STAFF',    icon: Icons.group_outlined),
    (tab: NavTab.patients,  label: 'PATIENTS', icon: Icons.person_add_alt_outlined),
    (tab: NavTab.reports,   label: 'INVENTORY',  icon: Icons.inventory),
    (tab: NavTab.settings,  label: 'SETTINGS', icon: Icons.tune_outlined),
  ];

  @override
  Widget build(BuildContext context) {
    final cubit = context.read<NavCubit>();

    return BlocBuilder<NavCubit, NavState>(
      builder: (context, state) {
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
                children: _items.map((item) {
                  final isActive = state.activeTab == item.tab;
                  return _NavItem(
                    icon: item.icon,
                    label: item.label,
                    isActive: isActive,
                    onTap: () => cubit.selectTab(item.tab),
                  );
                }).toList(),
              ),
            ),
          ),
        );
      },
    );
  }
}

class _NavItem extends StatelessWidget {
  const _NavItem({
    required this.icon,
    required this.label,
    required this.isActive,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final bool isActive;
  final VoidCallback onTap;


  static const _inactive = ColorResources.liteTextColor;
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: SizedBox(
        width: 65,
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