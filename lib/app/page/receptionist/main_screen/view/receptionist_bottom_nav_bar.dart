import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../widgets/app_bottom_nav_bar.dart';
import '../../../admin/admin_main_screen/repository/model';
import '../cubit/receptionist_nav_cubit.dart';

class ReceptionistBottomNavBar extends StatelessWidget {
  const ReceptionistBottomNavBar({super.key});

  @override
  Widget build(BuildContext context) {
    final cubit = context.read<ReceptionistNavCubit>();

    return BlocBuilder<ReceptionistNavCubit, ReceptionistNavState>(
      builder: (context, state) {
        return AppBottomNavBar(
          activeIndex: state.activeTab.index,
          items: [
            NavItemData(
              icon: Icons.grid_view_rounded,
              label: 'DASH',
              onTap: () => cubit.selectTab(ReceptionistTab.dashboard),
            ),
            NavItemData(
              icon: Icons.calendar_month,
              label: 'SCHEDULES',
              onTap: () => cubit.selectTab(ReceptionistTab.schedule),
            ),
            NavItemData(
              icon: Icons.person,
              label: 'PATIENTS',
              onTap: () => cubit.selectTab(ReceptionistTab.patients),
            ),
            NavItemData(
              icon: Icons.receipt,
              label: 'PAYMENTS',
              onTap: () => cubit.selectTab(ReceptionistTab.paymnets),
            ),

            NavItemData(
              icon: Icons.settings,
              label: 'SETTINGS',
              onTap: () => cubit.selectTab(ReceptionistTab.settings),
            ),
          ],
        );
      },
    );
  }
}
