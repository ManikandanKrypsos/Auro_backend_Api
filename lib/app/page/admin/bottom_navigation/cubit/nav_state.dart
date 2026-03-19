part of 'nav_cubit.dart';


enum NavTab { dashboard, staff, patients, reports, settings }

class NavState {
  final NavTab activeTab;

  const NavState({this.activeTab = NavTab.dashboard});

  NavState copyWith({NavTab? activeTab}) =>
      NavState(activeTab: activeTab ?? this.activeTab);
}