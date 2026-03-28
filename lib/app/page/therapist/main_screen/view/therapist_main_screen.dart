import 'package:aura/app/page/admin/patient/view/patient_list_screen.dart';
import 'package:aura/app/page/therapist/appointment/view/therapist_appointment_list_screen.dart';
import 'package:aura/app/page/therapist/dashboard/view/therapist_dashboard.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get/get.dart';


import '../../../../routes/names.dart';
import '../../../../widgets/alert_button.dart';
import '../cubit/therapist_nav_cubit.dart';
import '../view/receptionist_bottom_nav_bar.dart';

class TherapistMainScreen extends StatelessWidget {
  const TherapistMainScreen({super.key});

  static const _pages = <Widget>[
    TherapistDashboard(),
    TherapistAppointmentListScreen(),
    PatientsScreen(isReadOnly: true),
    ProductUsageScreen(),
    TherapistSettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => TherapistNavCubit(),
      child: BlocBuilder<TherapistNavCubit, TherapistNavState>(
        builder: (context, state) {
          return Scaffold(
            backgroundColor: const Color(0xFF0A0A0A),
            body: IndexedStack(
              index: state.activeTab.index,
              children: _pages,
            ),
            bottomNavigationBar: const TherapistBottomNavBar(),
          );
        },
      ),
    );
  }
}

class TherapistSettingsScreen extends StatelessWidget {
  const TherapistSettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return  Scaffold(body: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Center(child: Text('UPCOMING SCREEN')),
          const SizedBox(height: 20),
          AlertButton(onTap: () {
            Get.offAllNamed(PageRoutes.selectRoleScreen);
          }, text: 'LOG OUT'),
        ],
      ));
  }
}
class ProductUsageScreen extends StatelessWidget {
  const ProductUsageScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold();
  }
}

