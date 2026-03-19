import 'package:aura/app/page/admin/inventory/view/inventory_list_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../dashboard/view/admin_dashboard_screen.dart';
import '../../patient/view/patient_list_screen.dart';
import '../../settings/view/setting_screen.dart';
import '../../staff/view/staff_list_screen.dart';
import '../cubit/nav_cubit.dart';
import 'bottom_navigation_screen.dart';




class AdminMainScreen extends StatelessWidget {
  const AdminMainScreen({super.key});

  static const _pages = <Widget>[
    AdminDashboardScreen(),
    AdminStaffListScreen(),
    PatientsScreen(),
    InventoryScreen(),
    AdminSettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => NavCubit(),
      child: BlocBuilder<NavCubit, NavState>(
        builder: (context, state) {
          return Scaffold(
            backgroundColor: const Color(0xFF0A0A0A),
            body: IndexedStack(
              index: state.activeTab.index,
              children: _pages,
            ),
            bottomNavigationBar: const AdminBottomNavBar(),
          );
        },
      ),
    );
  }
}

