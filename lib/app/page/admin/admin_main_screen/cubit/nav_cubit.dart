
import 'package:flutter_bloc/flutter_bloc.dart';

part 'nav_state.dart';

class NavCubit extends Cubit<NavState> {
  NavCubit() : super(const NavState());

  void selectTab(NavTab tab) => emit(state.copyWith(activeTab: tab));
}