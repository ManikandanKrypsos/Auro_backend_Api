part of 'receptionist_nav_cubit.dart';

enum ReceptionistTab { dashboard, schedule, patients,paymnets, settings, }

class ReceptionistNavState {
  final ReceptionistTab activeTab;
  const ReceptionistNavState({this.activeTab = ReceptionistTab.dashboard});
}
