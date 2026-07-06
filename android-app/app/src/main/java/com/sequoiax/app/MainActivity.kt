package com.sequoiax.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import com.sequoiax.app.data.AppDatabase
import com.sequoiax.app.repository.StockRepository
import com.sequoiax.app.ui.AppViewModel
import com.sequoiax.app.ui.SequoiaApp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val repository = StockRepository(AppDatabase.create(this))
        val factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return AppViewModel(repository) as T
            }
        }
        setContent {
            val appViewModel: AppViewModel = viewModel(factory = factory)
            SequoiaApp(viewModel = appViewModel)
        }
    }
}
