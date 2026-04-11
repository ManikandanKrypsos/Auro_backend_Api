import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../widgets/app_bottom_nav_bar.dart';
import '../cubit/nav_cubit.dart';
import '../repository/model';

class AdminBottomNavBar extends StatelessWidget {
  const AdminBottomNavBar({super.key});

  @override
  Widget build(BuildContext context) {
    final cubit = context.read<NavCubit>();

    return BlocBuilder<NavCubit, NavState>(
      builder: (context, state) {
        return AppBottomNavBar(
          activeIndex: state.activeTab.index,
          items: [
            NavItemData(icon: Icons.grid_view_rounded,       label: 'DASH',      onTap: () => cubit.selectTab(NavTab.dashboard)),
            NavItemData(icon: Icons.group,           label: 'STAFF',     onTap: () => cubit.selectTab(NavTab.staff)),
            NavItemData(icon: Icons.person_add_alt,  label: 'PATIENTS',  onTap: () => cubit.selectTab(NavTab.patients)),
            NavItemData(icon: Icons.inventory,                label: 'INVENTORY', onTap: () => cubit.selectTab(NavTab.reports)),
            NavItemData(icon: Icons.settings,            label: 'SETTINGS',  onTap: () => cubit.selectTab(NavTab.settings)),
          ],
        );
      },
    );
  }
}