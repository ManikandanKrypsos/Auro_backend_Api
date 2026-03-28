import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../widgets/app_bottom_nav_bar.dart';
import '../../../admin/admin_main_screen/repository/model';
import '../cubit/therapist_nav_cubit.dart';

class TherapistBottomNavBar extends StatelessWidget {
  const TherapistBottomNavBar({super.key});

  @override
  Widget build(BuildContext context) {
    final cubit = context.read<TherapistNavCubit>();

    return BlocBuilder<TherapistNavCubit, TherapistNavState>(
      builder: (context, state) {
        return AppBottomNavBar(
          activeIndex: state.activeTab.index,
          items: [
            NavItemData(icon: Icons.grid_view_rounded,   label: 'DASH',     onTap: () => cubit.selectTab(TherapistTab.dashboard)),
            NavItemData(icon: Icons.list_alt,      label: 'SCHEDULES', onTap: () => cubit.selectTab(TherapistTab.schedule)),
            NavItemData(icon: Icons.person,      label: 'PATIENTS', onTap: () => cubit.selectTab(TherapistTab.patients)),
                        NavItemData(icon: Icons.medical_services  ,   label: 'PRODUCTS',     onTap: () => cubit.selectTab(TherapistTab.paymnets)),

            NavItemData(icon: Icons.settings,       label: 'SETTINGS', onTap: () => cubit.selectTab(TherapistTab.settings)),
          ],
   
        );
      },
    );
  }
}